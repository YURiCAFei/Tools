import os
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QMessageBox
)
from core.unpacker import unpack_all
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMessageBox
from core.task_runner import TaskRunner



class UnpackDialog(QDialog):
    def __init__(self, project_path, log_func, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量解压")

        self.project_path = project_path
        self.log_func = log_func

        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit(os.path.join(project_path, "unpack"))

        btn_input = QPushButton("选择压缩包路径")
        btn_output = QPushButton("选择保存路径")

        btn_input.clicked.connect(self.select_input_path)
        btn_output.clicked.connect(self.select_output_path)

        btn_ok = QPushButton("开始解压")
        btn_ok.clicked.connect(self.start_unpack)

        layout = QVBoxLayout()
        layout.addLayout(self._build_row("压缩包路径：", self.input_edit, btn_input))
        layout.addLayout(self._build_row("保存路径：", self.output_edit, btn_output))
        layout.addWidget(btn_ok)

        self.setLayout(layout)

    def _build_row(self, label_text, line_edit, button):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        layout.addWidget(line_edit)
        layout.addWidget(button)
        return layout

    def select_input_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择压缩文件路径")
        if folder:
            self.input_edit.setText(folder)

    def select_output_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择解压保存路径", self.output_edit.text())
        if folder:
            self.output_edit.setText(folder)


    def start_unpack(self):
        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()

        if not input_path or not os.path.isdir(input_path):
            QMessageBox.warning(self, "错误", "请输入有效的压缩文件路径")
            return

        if not output_path:
            QMessageBox.warning(self, "错误", "请输入保存路径")
            return

        os.makedirs(output_path, exist_ok=True)
        self.log_func(f"\n=====批量解压=====\n输入路径: {input_path}\n输出路径: {output_path}\n")

        parent = self.parent()
        logger = parent.logger if parent and hasattr(parent, "logger") else None

        # 启动后台线程任务
        self.thread = QThread()
        self.worker = TaskRunner(unpack_all, input_path, output_path, self.log_func)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: QMessageBox.information(self, "完成", "解压任务已完成！"))
        self.worker.failed.connect(self.thread.quit)
        self.worker.failed.connect(lambda msg: QMessageBox.critical(self, "错误", f"任务失败：{msg}"))

        self.thread.start()

        self.accept()  # 立刻关闭对话框
