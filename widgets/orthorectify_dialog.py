import os
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QHBoxLayout,
    QVBoxLayout, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QThread
from core.task_runner import TaskRunner
from core.orthorectifier import orthorectify_all
from core.thread_manager import ThreadManager


class OrthorectifyDialog(QDialog):
    def __init__(self, project_path, log_func, on_result, parent=None):
        super().__init__(parent)
        self.setWindowTitle("影像正射")
        self.project_path = project_path
        self.log_func = log_func
        self.on_result = on_result

        self.init_ui()

    def init_ui(self):
        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit()
        self.output_edit.setText(os.path.join(self.project_path, "orthorectified"))

        input_btn = QPushButton("选择影像路径")
        output_btn = QPushButton("选择保存路径")
        start_btn = QPushButton("开始正射")

        input_btn.clicked.connect(self.choose_input_path)
        output_btn.clicked.connect(self.choose_output_path)
        start_btn.clicked.connect(self.start_orthorectify)

        layout = QVBoxLayout()
        layout.addLayout(self._form_row("影像路径：", self.input_edit, input_btn))
        layout.addLayout(self._form_row("保存路径：", self.output_edit, output_btn))
        layout.addWidget(start_btn)
        self.setLayout(layout)

    def _form_row(self, label_text, line_edit, button):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        layout.addWidget(line_edit)
        layout.addWidget(button)
        return layout

    def choose_input_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择影像文件夹")
        if folder:
            self.input_edit.setText(folder)

    def choose_output_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_edit.setText(folder)

    def start_orthorectify(self):
        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()

        if not os.path.isdir(input_path):
            QMessageBox.warning(self, "错误", "请输入有效影像路径")
            return
        if not output_path:
            QMessageBox.warning(self, "错误", "请输入有效保存路径")
            return

        os.makedirs(output_path, exist_ok=True)
        self.log_func(f"\n=====影像正射=====\n输入路径: {input_path}\n输出路径: {output_path}\n")

        parent = self.parent()
        logger = parent.logger if parent and hasattr(parent, "logger") else None

        # 包装成无参函数以获取结果
        def wrapper():
            self.worker.result = orthorectify_all(input_path, output_path, self.log_func)

        self.thread = QThread()
        self.worker = TaskRunner(wrapper)
        self.worker.result = None
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: self.log_func("📌 所有影像正射完成"))
        self.worker.finished.connect(lambda: self.on_result(self.worker.result))

        self.worker.failed.connect(self.thread.quit)
        self.worker.failed.connect(lambda msg: QMessageBox.critical(self, "错误", f"任务失败：{msg}"))

        self.thread.start()

        ThreadManager.instance().register(self.thread)

        self.accept()
