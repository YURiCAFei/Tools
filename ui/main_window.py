import os
import datetime

from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QTextEdit, QListWidget, QVBoxLayout, QHBoxLayout, QSlider, \
    QFileDialog, QAction, QListWidgetItem, QMenuBar, QMenu, QDialog, QProgressBar, QPushButton, QSizePolicy, \
    QSplitter, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QThreadPool
from PyQt5.QtGui import QPixmap
from PyQt5 import QtGui

from ui.extract_boundary_dialog import ExtractBoundaryDialog
from ui.orthorectify_dialog import OrthorectifyDialog
from utils.decompress_worker import DecompressWorker
from utils.extract_boundary_worker import ExtractBoundaryTask
from utils.image_loader import ImageLoader
from utils.layer_manager import LayerManager
from utils.coord_converter import CoordConverter
from utils.file_process import decompress_process
from ui.decompress_dialog import DecompressDialog
from ui.satmap2gp_dialog import Satmap2GPDialog
from utils.Satmap2GPlidar import merge_csv_to_txt
from utils.orthorectify_worker import OrthoRectifyWorker
from utils.satmap2gp_worker import Satmap2GPWorker
from ui.lidar_downsample_dialog import LidarDownsampleDialog
from utils.downsample_worker import DownsampleWorker
from ui.map_canvas import MapViewWidget  # 新增地图显示器



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("工具软件")
        self.resize(1000, 600)

        self.transform = [None]
        self.crs = [None]
        self.scale_factor = 1.0

        self.init_widgets()
        self.init_menu_toolbar()

        self.layer_manager = LayerManager(self.layer_list, lambda : None)

        self.project_root = None
        self.project_log_file = None
        self.project_start_time = None
        self.function_log_buffer = []

    def create_image_display_widget(self):
        # self.image_label = QLabel()
        # self.image_label.setAlignment(Qt.AlignCenter)
        # self.image_label.setStyleSheet("border: 1px solid black; background-color: #f0f0f0;")
        # self.image_label.setMouseTracking(True)
        # self.image_label.mouseMoveEvent = self.mouse_move_event
        # self.image_label.wheelEvent = self.mouse_wheel_event
        # self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.map_canvas = MapViewWidget()
        self.map_canvas.setMinimumSize(300, 300)

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(300)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        self.zoom_slider.setFixedHeight(20)

        self.coord_label = QLabel("坐标: ")
        self.coord_label.setFixedHeight(20)
        self.map_canvas.coord_label = self.coord_label

        # 将地图和坐标放在上下分割中（垂直）
        map_layout = QVBoxLayout()
        map_layout.addWidget(self.map_canvas)
        map_layout.addWidget(self.zoom_slider)
        map_layout.addWidget(self.coord_label)

        widget = QWidget()
        widget.setLayout(map_layout)
        return widget

    def create_layer_widget(self):
        self.layer_list = QListWidget()
        self.layer_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.layer_list.customContextMenuRequested.connect(self.on_layer_context_menu)
        self.layer_list.itemChanged.connect(self.on_layer_check_changed)
        self.layer_list.itemDoubleClicked.connect(self.on_layer_double_clicked)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("图层列表"))
        layout.addWidget(self.layer_list)

        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def create_log_widget(self):
        self.cancel_button = QPushButton("取消任务")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_current_task)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("输出日志"))
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.log_output)

        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def init_widgets(self):
        layer_widget = self.create_layer_widget()
        image_widget = self.create_image_display_widget()
        log_widget = self.create_log_widget()

        # 图像显示区 + 日志区 = 垂直分割
        vertical_splitter = QSplitter(Qt.Vertical)
        vertical_splitter.addWidget(image_widget)
        vertical_splitter.addWidget(log_widget)
        vertical_splitter.setStretchFactor(0, 7)
        vertical_splitter.setStretchFactor(1, 3)
        vertical_splitter.setHandleWidth(3)

        # 左侧图层区 + 右侧显示区 = 水平分割
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(layer_widget)
        main_splitter.addWidget(vertical_splitter)
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 8)
        main_splitter.setHandleWidth(3)

        # ✅ 设置样式（不重新创建 splitter，而是设置样式）
        splitter_style = '''
            QSplitter::handle {
                background-color: #bbbbbb;
            }
            '''
        main_splitter.setStyleSheet(splitter_style)
        vertical_splitter.setStyleSheet(splitter_style)

        # 应用到界面
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_splitter)
        container.setLayout(layout)
        self.setCentralWidget(container)

    def init_menu_toolbar(self):
        menu_bar = QMenuBar(self)

        project_menu = QMenu("新建工程", self)
        new_project_action = QAction("选择工程目录", self)
        new_project_action.triggered.connect(self.select_project_folder)
        project_menu.addAction(new_project_action)
        menu_bar.addMenu(project_menu)

        file_menu = QMenu("文件处理", self)
        extract_action = QAction("解压", self)
        extract_action.triggered.connect(self.show_decompress_dialog)
        file_menu.addAction(extract_action)

        las_convert_menu = QMenu("激光数据处理", self)
        satmap2gp_action = QAction("Satmap2GP", self)
        satmap2gp_action.triggered.connect(self.show_satmap2gp_dialog)
        las_convert_menu.addAction(satmap2gp_action)

        downsample_action = QAction("激光点抽稀", self)
        downsample_action.triggered.connect(self.show_downsample_dialog)
        las_convert_menu.addAction(downsample_action)
        file_menu.addMenu(las_convert_menu)

        photogrammetry_menu = QMenu("摄影测量与遥感", self)

        # 正射影像按钮
        orthorectify_action = QAction("正射影像", self)
        orthorectify_action.triggered.connect(self.show_orthorectify_dialog)
        photogrammetry_menu.addAction(orthorectify_action)
        # 添加SHP子菜单
        shp_menu = QMenu("SHP", self)
        # 合并Shapefile（未实现)
        merge_shp_action = QAction("合并Shapefile（待实现）", self)
        merge_shp_action.setEnabled(False)
        shp_menu.addAction(merge_shp_action)
        # 边界提取
        boundary_action = QAction("边界SHP提取", self)
        boundary_action.triggered.connect(self.show_extract_boundary_dialog)
        shp_menu.addAction(boundary_action)

        photogrammetry_menu.addMenu(shp_menu)

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(photogrammetry_menu)
        self.setMenuBar(menu_bar)

    def cancel_current_task(self):
        if hasattr(self, "decompress_thread") and self.decompress_thread.isRunning():
            self.decompress_thread.stop()
            self.append_log("🟥 解压任务已请求终止")
            self.cancel_button.setEnabled(False)

        if hasattr(self, "downsample_thread") and self.downsample_thread.isRunning():
            self.downsample_thread.stop()
            self.append_log("🟥 抽稀任务已请求终止")
            self.cancel_button.setEnabled(False)

        if hasattr(self, "ortho_futures"):
            cancel_count = 0
            for fut in self.ortho_futures:
                if fut.cancel():
                    cancel_count += 1
            if cancel_count > 0:
                self.append_log("🟥 已取消 {cancel_count} 个尚未开始的正射任务")
            else:
                self.append_log("⚠️ 当前正射任务已开始执行，无法中断")
            self.cancel_button.setEnabled(False)

    # def render_combined_image(self):
    #     if not hasattr(self, "image_label") or self.image_label is None:
    #         return  # QLabel 被注释或移除，直接跳过
    #
    #     combined = self.layer_manager.render_combined()
    #     if combined:
    #         self.display_image(combined)
    #     else:
    #         self.image_label.clear()
    #
    # def display_image(self, pixmap: QPixmap):
    #     if hasattr(self, "image_label") and self.image_label:
    #         scaled = pixmap.scaled(self.image_label.size() * self.scale_factor, Qt.KeepAspectRatio,
    #                                Qt.SmoothTransformation)
    #         self.image_label.setPixmap(scaled)

    def update_zoom(self):
        self.scale_factor = self.zoom_slider.value() / 100.0
        # self.render_combined_image()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # self.render_combined_image()

    def mouse_move_event(self, event):
        if self.transform[0] and self.crs[0]:
            x, y = event.pos().x(), event.pos().y()
            lon, lat = CoordConverter.to_wgs84(self.transform[0], self.crs[0], x, y)
            self.coord_label.setText(f"坐标: {lon:.6f}, {lat:.6f}")

    def show_decompress_dialog(self):
        if not self.check_project_ready("解压"):
            return
        dialog = DecompressDialog(self)
        if dialog.exec_():
            file_path, folder_path, output_path = dialog.get_paths()
            if not output_path:
                self.append_log("❌ 保存路径不能为空")
                return
            input_path = file_path or folder_path
            if not input_path:
                self.append_log("❌ 请至少选择一个压缩文件或文件夹")
                return

            self.append_log("🟡 解压开始...")
            self.cancel_button.setVisible(True)
            self.cancel_button.setEnabled(True)

            self.decompress_thread = DecompressWorker(
                input_path, output_path, decompress_func=decompress_process
            )
            self.decompress_thread.progress_update.connect(self.append_log)
            self.decompress_thread.finished.connect(self.on_decompression_finished)
            self.decompress_thread.stopped.connect(self.on_decompression_stopped)
            self.decompress_thread.start()

    def on_decompression_finished(self):
        self.append_log("✅ 解压完成")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)

    def on_decompression_stopped(self):
        self.append_log("🟥 解压被用户取消")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)

    def show_satmap2gp_dialog(self):
        if not self.check_project_ready("Satmap2GP"):
            return
        try:
            dialog = Satmap2GPDialog(self)
            if dialog.exec_():
                lidar_path, save_path, file_name = dialog.get_inputs()
                if not os.path.isdir(lidar_path):
                    self.append_log("❌ 激光路径无效")
                    return
                if not os.path.isdir(save_path):
                    self.append_log("❌ 保存路径无效")
                    return
                self.append_log(f"🛰️ 激光路径: {lidar_path}")
                self.append_log(f"📁 保存路径: {save_path}")
                self.append_log(f"📄 输出文件名: {file_name}")

                self.append_log("🛰️ Satmap2GP 开始执行...")

                self.satmap2gp_thread = Satmap2GPWorker(lidar_path, save_path, file_name)
                self.satmap2gp_thread.progress.connect(self.append_log)
                self.satmap2gp_thread.finished.connect(lambda: self.append_log("✅ Satmap2GP 完成"))
                self.satmap2gp_thread.start()
        except Exception as e:
            print("[ERROR] Satmap2GPDialog 崩溃", e)

    def update_map_layer(self, filename, pixmap, transform):
        print(f"[DEBUG] ✅ 进入 update_map_layer() ：{filename}")
        name = os.path.basename(filename)
        print(f"[UI更新] 图层名: {name}")

        if pixmap:
            print(f"[UI更新] pixmap 尺寸: {pixmap.width()}x{pixmap.height()}")
        else:
            print(f"[UI更新] pixmap 为空！")

        if transform:
            print(f"[UI更新] transform 左上角: ({transform.c}, {transform.f})")
        else:
            print(f"[UI更新] transform 为 None！")

        if pixmap and transform:
            self.map_canvas.add_layer(name, pixmap, transform)
            self.map_canvas.fitInView(self.map_canvas.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            # self.layer_list.addItem(name)
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.layer_list.addItem(item)
        else:
            self.append_log(f"❌ 地图图像加载失败: {filename}")


    def mouse_wheel_event(self, event):
        delta = event.angleDelta().y()
        step = 10 if delta > 0 else -10
        current = self.zoom_slider.value()
        new_value = max(self.zoom_slider.minimum(), min(self.zoom_slider.maximum(), current + step))
        self.zoom_slider.setValue(new_value)

    def show_downsample_dialog(self):
        if not self.check_project_ready("激光点抽稀"):
            return
        dialog = LidarDownsampleDialog(self)
        if dialog.exec_():
            inputs = dialog.get_inputs()
            method = inputs["method"]
            param = inputs["param"]
            input_path = inputs["input_path"]
            output_path = inputs["output_path"]
            filename = inputs["filename"]

            self.append_log("🟡 开始激光点抽稀任务...")
            self.cancel_button.setVisible(True)
            self.cancel_button.setEnabled(True)

            self.downsample_thread = DownsampleWorker(
                input_path=input_path,
                output_path=output_path,
                method=method,
                param=param,
                filename=filename
            )
            self.downsample_thread.progress.connect(self.append_log)
            self.downsample_thread.finished.connect(self.on_downsample_finished)
            self.downsample_thread.stopped.connect(self.on_downsample_stopped)
            self.downsample_thread.start()

    def on_downsample_finished(self):
        self.append_log("✅ 抽稀完成")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)

    def on_downsample_stopped(self):
        self.append_log("🟥 抽稀被取消")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)

    def select_project_folder(self):
        path = QFileDialog.getExistingDirectory(self, "选择工程文件夹")
        if path:
            self.project_root = path
            self.project_start_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            self.project_log_file = os.path.join(self.project_root, f"log_{self.project_start_time}.txt")
            self.append_log(f"📁 已设置工程目录：{self.project_root}")

    def check_project_ready(self, feature_name: str) -> bool:
        if not self.project_root:
            QMessageBox.warning(self, "提示", "请新建工程")
            return False
        self.function_log_buffer.append(f"===== {feature_name} =====")
        return True

    def append_log(self, msg: str):
        if hasattr(self, "log_output") and self.log_output:
            self.log_output.append(msg)

            # 限制最大行数，超出则删除前面的内容
            max_lines = 1000
            if self.log_output.document().blockCount() > max_lines:
                cursor = self.log_output.textCursor()
                cursor.movePosition(QtGui.QTextCursor.Start)
                cursor.select(QtGui.QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()

            self.log_output.moveCursor(QtGui.QTextCursor.End)
            self.log_output.ensureCursorVisible()

        self.function_log_buffer.append(msg)

    def closeEvent(self, event):
        active_tasks = []
        if hasattr(self, "decompress_thread") and self.decompress_thread.isRunning():
            active_tasks.append("解压")
        if hasattr(self, "downsample_thread") and self.downsample_thread.isRunning():
            active_tasks.append("激光点抽稀")
        if active_tasks:
            task_list = "、".join(active_tasks)
            try:
                reply = QMessageBox.question(
                    self,
                    "仍有任务在运行",
                    f"当前存在正在进行的任务：{task_list}。\n确定要退出吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    event.ignore()
                    return
            except Exception as e:
                print(f"[关闭提示失败] {e}")
                event.ignore()
                return
        try:
            if self.project_log_file and self.function_log_buffer:
                with open(self.project_log_file, 'w', encoding='utf-8') as f:
                    f.write("\n\n".join(self.function_log_buffer))
        except Exception as e:
            print(f"[写入日志失败] {e}")

        # 清理正射影像线程池
        try:
            if hasattr(self, "executor"):
                self.executor.shutdown(wait=False, cancel_futures=True)
                self.append_log("🛑 正射线程池已关闭")
        except Exception as e:
            print(f"[关闭线程池失败] {e}")
        super().closeEvent(event)

    def show_orthorectify_dialog(self):
        import concurrent.futures
        from utils.orthorectify_logic import process_single_image, MAX_WORKERS

        if not self.check_project_ready("正射影像"):
            return

        dialog = OrthorectifyDialog(self)
        if hasattr(self, 'project_root') and self.project_root:
            default_output = os.path.join(self.project_root, "orthorectified")
            os.makedirs(default_output, exist_ok=True)
            dialog.output_edit.setText(default_output)

        if dialog.exec_():
            input_dir, output_dir = dialog.get_paths()
            interp_method = dialog.get_interp_method()

            if not os.path.isdir(input_dir) or not os.path.isdir(output_dir):
                self.append_log("❌ 输入或输出目录无效")
                return

            self.append_log(f"📂 正射输入目录: {input_dir}")
            self.append_log(f"📁 正射输出目录: {output_dir}")
            self.append_log(f"🔧 插值方式: {interp_method}")
            self.cancel_button.setVisible(True)
            self.cancel_button.setEnabled(False)

            self.ortho_results = []
            self.ortho_futures = []
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

            def log_wrapper(msg):
                self.append_log(msg)

            def done_callback(future):
                try:
                    output_path = future.result()
                    self.ortho_results.append(output_path)

                    from utils.image_loader import ImageLoader

                    def on_loaded(filename, pixmap, transform):
                        print(f"[加载回调] 文件: {filename}")
                        self.update_map_layer(filename, pixmap, transform)

                    ImageLoader.load_async_with_transform(output_path, on_loaded)

                except Exception as e:
                    self.append_log(f"❌ 正射异常: {e}")
                finally:
                    if len(self.ortho_results) == self.total_tasks:
                        self.append_log("✅ 所有正射影像处理完成")
                        self.cancel_button.setEnabled(False)
                        self.cancel_button.setVisible(False)

            self.total_tasks = 0
            for fname in os.listdir(input_dir):
                if fname.lower().endswith(('.tif', '.tiff', '.TIF', '.TIFF')):
                    base = os.path.splitext(fname)[0]
                    image_path = os.path.join(input_dir, fname)
                    rpc_path = os.path.join(input_dir, base + '_rpc.txt')
                    if os.path.exists(rpc_path):
                        future = self.executor.submit(
                            process_single_image,
                            image_path,
                            rpc_path,
                            output_dir,
                            log_wrapper,
                            interp_method  # ✅ 加入插值参数
                        )
                        future.add_done_callback(done_callback)
                        self.ortho_futures.append(future)
                        self.total_tasks += 1
                    else:
                        self.append_log(f"⚠️ 缺少 RPC 文件: {base}_rpc.txt")

            if self.total_tasks == 0:
                self.append_log("⚠️ 未找到可处理的影像")

    def on_layer_check_changed(self, item):
        name = item.text()
        visible = item.checkState() == Qt.Checked
        self.map_canvas.set_layer_visible(name, visible)

    def on_layer_double_clicked(self, item):
        name = item.text()
        self.map_canvas.center_on_layer(name)

    def on_layer_context_menu(self, pos):
        item = self.layer_list.itemAt(pos)
        if item:
            name = item.text()
            menu = QMenu(self)
            delete_action = menu.addAction("删除图层")
            action = menu.exec_(self.layer_list.mapToGlobal(pos))
            if action == delete_action:
                self.map_canvas.remove_layer(name)
                self.layer_list.takeItem(self.layer_list.row(item))

    def show_extract_boundary_dialog(self):
        if not self.check_project_ready("边界SHP提取"):
            return
        default_save = os.path.join(self.project_root, "boundary")
        dialog = ExtractBoundaryDialog(default_save, self.extract_boundaries, self)
        dialog.exec_()

    def extract_boundaries(self, in_dir, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        self.append_log(f"📦 正在批量提取 TIFF 边界：{in_dir} → {out_dir}")

        suffixes = ('.tif', '.tiff', '.TIF', '.TIFF')
        files = [f for f in os.listdir(in_dir) if f.endswith(suffixes)]

        self.boundary_total = len(files)
        self.boundary_done = 0
        self.thread_pool = QThreadPool.globalInstance()

        for f in files:
            input_path = os.path.join(in_dir, f)
            name, _ = os.path.splitext(f)
            output_path = os.path.join(out_dir, f"{name}.shp")

            task = ExtractBoundaryTask(input_path, output_path)
            task.signals.finished.connect(self.on_boundary_done)
            self.thread_pool.start(task)

    def on_boundary_done(self, msg):
        self.append_log(msg)
        self.boundary_done += 1
        if self.boundary_done == self.boundary_total:
            self.append_log("🎉 所有边界提取任务完成！")

