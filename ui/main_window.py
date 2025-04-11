import os
import datetime

from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QTextEdit, QListWidget, QVBoxLayout, QHBoxLayout, QSlider, \
    QFileDialog, QToolBar, QAction, QListWidgetItem, QMenuBar, QMenu, QDialog, QProgressBar, QPushButton, QSizePolicy, \
    QSplitter, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from utils.decompress_worker import DecompressWorker
from utils.image_loader import ImageLoader
from utils.layer_manager import LayerManager
from utils.coord_converter import CoordConverter
from utils.file_process import decompress_process
from ui.decompress_dialog import DecompressDialog
from ui.satmap2gp_dialog import Satmap2GPDialog
from utils.Satmap2GPlidar import merge_csv_to_txt
from utils.satmap2gp_worker import Satmap2GPWorker
from ui.lidar_downsample_dialog import LidarDownsampleDialog
from utils.downsample_worker import DownsampleWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("工具软件")
        self.resize(1000, 600)

        # 初始化状态容器
        self.transform = [None]
        self.crs = [None]
        self.scale_factor = 1.0

        # 初始化 UI 元素
        self.init_widgets()
        self.init_menu_toolbar()

        # 初始化图层管理器
        self.layer_manager = LayerManager(self.layer_list, self.render_combined_image)

        # 工程相关
        self.project_root = None
        self.project_log_file = None
        self.project_start_time = None
        self.function_log_buffer = []
        self.init_project_button()

    def create_image_display_widget(self):
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid black; background-color: #f0f0f0;")
        self.image_label.setMouseTracking(True)
        self.image_label.mouseMoveEvent = self.mouse_move_event
        self.image_label.wheelEvent = self.mouse_wheel_event
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(300)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        self.zoom_slider.setFixedHeight(20)

        self.coord_label = QLabel("坐标: ")
        self.coord_label.setFixedHeight(20)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("图片显示区"))
        layout.addWidget(self.image_label)
        layout.addWidget(self.zoom_slider)
        layout.addWidget(self.coord_label)

        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def create_layer_widget(self):
        self.layer_list = QListWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("图层列表"))
        layout.addWidget(self.layer_list)

        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def create_log_widget(self):
        self.cancel_button = QPushButton("取消解压")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_decompression)

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

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(image_widget)
        right_splitter.addWidget(log_widget)
        right_splitter.setStretchFactor(0, 7)
        right_splitter.setStretchFactor(1, 3)
        right_splitter.setHandleWidth(2)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(layer_widget)
        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 8)
        main_splitter.setHandleWidth(2)

        container = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(main_splitter)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setStyleSheet("""
                QSplitter::handle {
                    background-color: #888888;
                    border: 1px solid #666666;
                    margin: 0px;
                }
                QSplitter::handle:horizontal {
                    height: 2px;
                }
                QSplitter::handle:vertical {
                    width: 2px;
                }
            """)

    def init_project_button(self):
        new_project_action = QAction("新建工程", self)
        new_project_action.triggered.connect(self.select_project_folder)
        self.menuBar().addAction(new_project_action)

    def init_menu_toolbar(self):
        menu_bar = QMenuBar(self)
        # 文件处理菜单，用于一些基本的文件处理
        file_menu = QMenu("文件处理", self)

        extract_action = QAction("解压", self)
        extract_action.triggered.connect(self.show_decompress_dialog)
        file_menu.addAction(extract_action)

        # 激光格式转换，实现激光格式转换
        las_convert_menu = QMenu("激光数据处理", self)

        satmap2gp_action = QAction("Satmap2GP", self)
        # satmap2gp_action.setEnabled(False)
        satmap2gp_action.triggered.connect(self.show_satmap2gp_dialog)
        las_convert_menu.addAction(satmap2gp_action)

        downsample_action = QAction("激光点抽稀", self)
        # downsample_action.setEnabled(False)
        downsample_action.triggered.connect(self.show_downsample_dialog)
        las_convert_menu.addAction(downsample_action)

        # 摄影测量与遥感菜单
        photogrammetry_menu = QMenu("摄影测量与遥感", self)

        merge_shp_action = QAction("合并Shapefile（待实现）", self)
        merge_shp_action.setEnabled(False)
        photogrammetry_menu.addAction(merge_shp_action)

        file_menu.addMenu(las_convert_menu)

        # 为menu_bar添加菜单
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(photogrammetry_menu)
        self.setMenuBar(menu_bar)

    def render_combined_image(self):
        combined = self.layer_manager.render_combined()
        if combined:
            self.display_image(combined)
        else:
            self.image_label.clear()

    def display_image(self, pixmap: QPixmap):
        scaled = pixmap.scaled(self.image_label.size() * self.scale_factor, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)

    def update_zoom(self):
        self.scale_factor = self.zoom_slider.value() / 100.0
        self.render_combined_image()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.render_combined_image()

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
            self.progress_bar.setValue(0)
            self.cancel_button.setVisible(True)
            self.cancel_button.setEnabled(True)

            self.decompress_thread = DecompressWorker(
                input_path, output_path, decompress_func=decompress_process
            )
            self.decompress_thread.progress_update.connect(self.append_log)
            self.decompress_thread.finished.connect(self.on_decompression_finished)
            self.decompress_thread.stopped.connect(self.on_decompression_stopped)
            self.decompress_thread.start()

    def cancel_decompression(self):
        if hasattr(self, 'decompress_thread') and self.decompress_thread.isRunning():
            self.decompress_thread.stop()
            self.cancel_button.setEnabled(False)

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

    def mouse_wheel_event(self, event):
        delta = event.angleDelta().y()
        step = 10 if delta > 0 else -10
        current = self.zoom_slider.value()
        new_value = max(self.zoom_slider.minimum(), min(self.zoom_slider.maximum(), current + step))
        self.zoom_slider.setValue(new_value)

    def show_downsample_dialog(self):
        dialog = LidarDownsampleDialog(self)
        if dialog.exec_():
            inputs = dialog.get_inputs()
            method = inputs["method"]
            param = inputs["param"]
            input_path = inputs["input_path"]
            output_path = inputs["output_path"]
            filename = inputs["filename"]

            if not self.check_project_ready("激光点抽稀"):
                return

            self.append_log("🟡 开始激光点抽稀任务...")

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
        self.function_log_buffer.append(msg)

    def closeEvent(self, event):
        # 检查是否有后台线程在运行
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

        # 安全写入日志
        try:
            if self.project_log_file and self.function_log_buffer:
                with open(self.project_log_file, 'w', encoding='utf-8') as f:
                    f.write("\n\n".join(self.function_log_buffer))
        except Exception as e:
            print(f"[写入日志失败] {e}")

        super().closeEvent(event)

    def on_downsample_finished(self):
        self.append_log("✅ 抽稀完成")

    def on_downsample_stopped(self):
        self.append_log("🟥 抽稀被取消")


