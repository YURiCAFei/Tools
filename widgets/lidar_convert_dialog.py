import os
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QMessageBox
)
from core.lidar_converter import convert_all_lidar_folders
from PyQt5.QtCore import QThread
from core.task_runner import TaskRunner
from core.thread_manager import ThreadManager


class LidarConvertDialog(QDialog):
    def __init__(self, project_path, log_func, parent=None):
        super().__init__(parent)
        self.setWindowTitle("激光格式转换")

        self.project_path = project_path
        self.log_func = log_func

        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit(os.path.join(project_path, "lidar_convert"))

        btn_input = QPushButton("选择激光路径")
        btn_output = QPushButton("选择保存路径")
        btn_run = QPushButton("开始转换")

        btn_input.clicked.connect(self.select_input_path)
        btn_output.clicked.connect(self.select_output_path)
        btn_run.clicked.connect(self.start_convert)

        layout = QVBoxLayout()
        layout.addLayout(self._build_row("激光路径：", self.input_edit, btn_input))
        layout.addLayout(self._build_row("保存路径：", self.output_edit, btn_output))
        layout.addWidget(btn_run)

        self.setLayout(layout)

    def _build_row(self, label_text, line_edit, button):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        layout.addWidget(line_edit)
        layout.addWidget(button)
        return layout

    def select_input_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择激光点云路径")
        if folder:
            self.input_edit.setText(folder)

    def select_output_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择保存路径", self.output_edit.text())
        if folder:
            self.output_edit.setText(folder)

    def show_success_and_close(self):
        QMessageBox.information(self, "完成", "激光格式转换任务已完成！")
        self.accept()

    def start_convert(self):
        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()

        if not os.path.isdir(input_path):
            QMessageBox.warning(self, "错误", "请选择有效的激光路径")
            return
        if not output_path:
            QMessageBox.warning(self, "错误", "请选择输出路径")
            return

        os.makedirs(output_path, exist_ok=True)
        self.log_func(f"\n=====激光格式转换=====\n输入路径: {input_path}\n输出路径: {output_path}\n")

        parent = self.parent()
        logger = parent.logger if parent and hasattr(parent, "logger") else None

        # 使用后台线程执行转换任务
        self.thread = QThread()
        self.worker = TaskRunner(convert_all_lidar_folders, input_path, output_path, self.log_func, logger)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: QMessageBox.information(self, "完成", "激光格式转换任务完成！"))
        self.worker.failed.connect(self.thread.quit)
        self.worker.failed.connect(lambda msg: QMessageBox.critical(self, "错误", f"任务失败：{msg}"))

        self.thread.start()

        ThreadManager.instance().register(self.thread)

        self.accept() # 立刻关闭对话框
