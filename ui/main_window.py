import os

from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QTextEdit, QListWidget, QVBoxLayout, QHBoxLayout, QSlider, \
    QFileDialog, QToolBar, QAction, QListWidgetItem, QMenuBar, QMenu, QDialog, QProgressBar, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from utils.decompress_worker import DecompressWorker
from utils.image_loader import ImageLoader
from utils.layer_manager import LayerManager
from utils.coord_converter import CoordConverter
from utils.file_process import decompress_process
from ui.decompress_dialog import DecompressDialog
from ui.satmap2gp_dialog import Satmap2GPDialog


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

    def init_widgets(self):
        self.layer_list = QListWidget()
        self.layer_list.setMaximumWidth(200)

        self.image_label = QLabel()
        self.image_label.setFixedHeight(350)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid black; background-color: #f0f0f0;")
        self.image_label.setMouseTracking(True)
        self.image_label.mouseMoveEvent = self.mouse_move_event

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(300)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.update_zoom)

        self.coord_label = QLabel("坐标: ")

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setFormat("0.0%")
        self.progress_bar.setValue(0)

        self.cancel_button = QPushButton("取消解压")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_decompression)

        # 布局
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("图层列表"))
        left_layout.addWidget(self.layer_list)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("图片显示区"))
        right_layout.addWidget(self.image_label)
        right_layout.addWidget(self.zoom_slider)
        right_layout.addWidget(self.coord_label)
        right_layout.addWidget(QLabel("输出日志"))
        right_layout.addWidget(self.log_output)
        # right_layout.addWidget(self.progress_bar)
        # right_layout.addWidget(self.cancel_button)
        # 解压进度条 + 右对齐按钮
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)

        # 占位拉伸 + 按钮右对齐
        progress_layout.addStretch()
        progress_layout.addWidget(self.cancel_button)

        self.cancel_button.setVisible(False)  # 默认隐藏
        self.cancel_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        right_layout.addLayout(progress_layout)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def init_menu_toolbar(self):
        menu_bar = QMenuBar(self)
        # 文件处理菜单，用于一些基本的文件处理
        file_menu = QMenu("文件处理", self)

        extract_action = QAction("解压", self)
        extract_action.triggered.connect(self.show_decompress_dialog)
        file_menu.addAction(extract_action)

        # 激光格式转换，实现激光格式转换
        las_convert_menu = QMenu("激光格式转换", self)

        satmap2gp_action = QAction("Satmap2GP", self)
        # satmap2gp_action.setEnabled(False)
        satmap2gp_action.triggered.connect(self.show_satmap2gp_dialog)
        las_convert_menu.addAction(satmap2gp_action)

        gp2satmap_action = QAction("GP2Satmap", self)
        gp2satmap_action.setEnabled(False)
        las_convert_menu.addAction(gp2satmap_action)

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
        dialog = DecompressDialog(self)
        if dialog.exec_():
            file_path, folder_path, output_path = dialog.get_paths()
            if not output_path:
                self.log_output.append("❌ 保存路径不能为空")
                return
            input_path = file_path or folder_path
            if not input_path:
                self.log_output.append("❌ 请至少选择一个压缩文件或文件夹")
                return

            self.log_output.append("🟡 解压开始...")
            self.progress_bar.setValue(0)
            self.cancel_button.setVisible(True)
            self.cancel_button.setEnabled(True)

            self.decompress_thread = DecompressWorker(
                input_path, output_path, decompress_func=decompress_process
            )
            self.decompress_thread.progress_update.connect(self.log_output.append)
            self.decompress_thread.progress_percent.connect(self.update_progress_bar)
            self.decompress_thread.finished.connect(self.on_decompression_finished)
            self.decompress_thread.stopped.connect(self.on_decompression_stopped)
            self.decompress_thread.start()

    def cancel_decompression(self):
        if hasattr(self, 'decompress_thread') and self.decompress_thread.isRunning():
            self.decompress_thread.stop()
            self.cancel_button.setEnabled(False)

    def on_decompression_finished(self):
        self.log_output.append("✅ 解压完成")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)
        self.progress_bar.setValue(1000)
        self.progress_bar.setFormat("100.0%")

    def on_decompression_stopped(self):
        self.log_output.append("🟥 解压被用户取消")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)
        self.progress_bar.setValue(0)

    def update_progress_bar(self, percent: float):
        """进度条更新：小数百分比 + 平滑显示"""
        scaled = int(percent * 10)  # 比如 65.3 → 653
        self.progress_bar.setValue(scaled)
        self.progress_bar.setFormat(f"{percent:.1f}%")

    def show_satmap2gp_dialog(self):
        dialog = Satmap2GPDialog(self)
        if dialog.exec_():
            lidar_path, save_path, file_name = dialog.get_inputs()
            self.log_output.append(f"🛰️ 激光路径: {lidar_path}")
            self.log_output.append(f"📁 保存路径: {save_path}")
            self.log_output.append(f"📄 输出文件名: {file_name}")
