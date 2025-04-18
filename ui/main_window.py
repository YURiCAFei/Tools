import os

from PyQt5.QtGui import QCloseEvent, QPainter
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QListWidget, QTextEdit, QLabel,
    QVBoxLayout, QHBoxLayout, QAction, QFileDialog, QMessageBox, QGroupBox, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread

from core.layer_batch_loader import load_layers_batch
from core.layer_loader import LayerLoader
from core.log_manager import LogManager
from core.thread_manager import ThreadManager
from widgets.downsample_dialog import DownsampleDialog
from widgets.map_canvas import MapCanvas
from widgets.orthorectify_dialog import OrthorectifyDialog
from widgets.unpack_dialog import UnpackDialog
from widgets.lidar_convert_dialog import LidarConvertDialog
from qgis.core import QgsRasterLayer, QgsProject


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("工具软件")
        self.resize(1000, 600)

        self.project_path = None

        # 创建主界面布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 左侧图层列表
        layer_group = QGroupBox("图层")
        layer_layout = QVBoxLayout()
        self.layer_list = QListWidget()
        layer_layout.addWidget(self.layer_list)
        layer_group.setLayout(layer_layout)
        layer_group.setMinimumWidth(150)
        layer_group.setMaximumWidth(200)
        self.layer_list.itemChanged.connect(self.toggle_layer_visibility)
        self.layer_list.itemChanged.connect(self.update_canvas_layers)
        main_layout.addWidget(layer_group)

        # 中间地图画布
        canvas_group = QGroupBox("地图显示")
        canvas_layout = QVBoxLayout()
        self.map_canvas = MapCanvas()
        self.map_canvas.setCanvasColor(Qt.white)
        self.map_canvas.setCachingEnabled(True)
        self.map_canvas.setRenderFlag(True)
        canvas_layout.addWidget(self.map_canvas)
        canvas_group.setLayout(canvas_layout)
        main_layout.addWidget(canvas_group)

        # 右侧日志输出
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        log_group.setMinimumWidth(200)
        log_group.setMaximumWidth(300)
        main_layout.addWidget(log_group)

        # 底部状态栏
        self.status_label = QLabel("坐标:")
        self.statusBar().addWidget(self.status_label)

        # 菜单栏
        self._create_menus()

        # 日志
        self.logger = None

    def _create_menus(self):
        menu_bar = self.menuBar()

        action_new_project = QAction("新建工程", self)
        action_new_project.triggered.connect(self.create_project)
        menu_bar.addAction(action_new_project)

        self.menu_file = menu_bar.addMenu("文件处理")
        self.menu_photogrammetry = menu_bar.addMenu("摄影测量与遥感")

        # 批量解压
        action_unpack = QAction("批量解压", self)
        action_unpack.triggered.connect(self.show_unpack_dialog)
        self.menu_file.addAction(action_unpack)

        # 激光数据处理
        self.menu_lidar = self.menu_file.addMenu("激光处理")
        action_lidar_convert = QAction("激光格式转换", self)
        action_lidar_convert.triggered.connect(self.show_lidar_convert_dialog)
        self.menu_lidar.addAction(action_lidar_convert)
        action_lidar_sample = QAction("点云抽稀", self)
        action_lidar_sample.triggered.connect(self.show_downsample_dialog)
        self.menu_lidar.addAction(action_lidar_sample)

        # 影像正射
        action_ortho = QAction("影像正射", self)
        action_ortho.triggered.connect(self.show_orthorectify_dialog)
        self.menu_photogrammetry.addAction(action_ortho)

    def create_project(self):
        folder = QFileDialog.getExistingDirectory(self, "选择工程文件夹")
        if folder:
            self.project_path = folder
            self.logger = LogManager(self.project_path)
            self.log(f"=====新建工程=====\n工程路径: {folder}\n")
        else:
            if self.project_path is None:
                QMessageBox.information(self, "提示", "请选择一个文件夹作为工程目录")
            else:
                QMessageBox.information(self, "提示", "工程目录为：" + self.project_path)

    def show_unpack_dialog(self):
        if not self.project_path:
            QMessageBox.warning(self, "提示", "请先新建工程！")
            return

        dialog = UnpackDialog(self.project_path, self.log, self)
        dialog.exec_()

    def log(self, text):
        self.log_output.append(text)
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())
        if self.logger:
            self.logger.log(text, to_console=False)

    def show_lidar_convert_dialog(self):
        if not self.project_path:
            QMessageBox.warning(self, "提示", "请先新建工程！")
            return

        dialog = LidarConvertDialog(self.project_path, self.log, self)
        dialog.exec_()

    def show_downsample_dialog(self):
        if not self.project_path:
            QMessageBox.warning(self, "提示", "请先新建工程！")
            return

        dialog = DownsampleDialog(self.project_path, self.log, self)
        dialog.exec_()

    def load_images(self, image_paths):
        for path in image_paths:
            name = os.path.basename(path)
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, path)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)  # 懒加载
            self.layer_list.insertItem(0, item)
            self.log(f"🖼 注册图层（等待加载）：{name}")

    def show_orthorectify_dialog(self):
        if not self.project_path:
            QMessageBox.warning(self, "提示", "请先新建工程！")
            return

        dialog = OrthorectifyDialog(
            self.project_path,
            self.log,
            lambda paths: load_layers_batch(
                layer_paths=paths,
                canvas=self.map_canvas,
                layer_list_widget=self.layer_list,
                log_func=self.log
            ),
            self
        )
        dialog.exec_()

    def toggle_layer_visibility(self, item):
        path = item.data(Qt.UserRole)
        visible = item.checkState() == Qt.Checked

        if visible:
            self.log(f"🔄 开始加载图层：{path}")

            # 为每个图层单独创建线程和worker并保存引用
            thread = QThread()
            worker = LayerLoader(path)
            worker.moveToThread(thread)

            # 保持引用，防止被回收
            if not hasattr(self, "_layer_threads"):
                self._layer_threads = []
            self._layer_threads.append((thread, worker))

            thread.started.connect(worker.run)
            worker.finished.connect(thread.quit)
            worker.finished.connect(lambda layer, extent, p=path: self._on_layer_loaded(layer, extent, item))
            worker.failed.connect(thread.quit)
            worker.failed.connect(lambda p, err: self.log(f"❌ 加载失败: {p} → {err}"))

            thread.start()
        else:
            self._remove_layer(item.text())

    def update_canvas_layers(self):
        visible_layers = []
        layer_names = [
            self.layer_list.item(i).text()
            for i in range(self.layer_list.count())
            if self.layer_list.item(i).checkState() == Qt.Checked
        ]

        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() in layer_names:
                visible_layers.append(layer)

        self.map_canvas.setLayers(visible_layers)
        self.map_canvas.refresh()

    def _on_layer_loaded(self, layer, extent, item):
        QgsProject.instance().addMapLayer(layer)

        # 🧠 构建金字塔（提高加载大图时的滚动/缩放响应速度）
        try:
            if layer.dataProvider().supportsPyramids():
                res = layer.dataProvider().buildPyramid()
                if not res:
                    self.log(f"⚠️ 构建金字塔失败：{layer.name()}")
                else:
                    self.log(f"📐 已为图层构建金字塔：{layer.name()}")
        except Exception as e:
            self.log(f"⚠️ 构建金字塔异常：{e}")

        # 图层渲染
        current_layers = self.map_canvas.layers()
        if layer not in current_layers:
            current_layers.insert(0, layer)
            self.map_canvas.setLayers(current_layers)
        self.map_canvas.setExtent(extent)
        self.map_canvas.refresh()

        self.log(f"✅ 加载成功：{layer.name()}")

    def _remove_layer(self, layer_name):
        for lyr in QgsProject.instance().mapLayers().values():
            if lyr.name() == layer_name:
                QgsProject.instance().removeMapLayer(lyr.id())
                self.map_canvas.refresh()
                self.log(f"🗑 已移除图层：{layer_name}")
                break

    def closeEvent(self, event: QCloseEvent):
        try:
            # ✅ 自动清理所有已注册线程
            ThreadManager.instance().cleanup()

            # ✅ 日志刷新（如有）
            if hasattr(self, "logger") and hasattr(self.logger, "flush"):
                self.logger.flush()
        except Exception as e:
            print(f"[!] 关闭主程序时异常: {e}")

        event.accept()

