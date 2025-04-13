from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
)
import os

class ExtractBoundaryDialog(QDialog):
    def __init__(self, default_save_path, callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle("边界SHP提取")
        self.callback = callback
        self.save_path = default_save_path

        layout = QVBoxLayout()

        # 输入路径
        self.input_path_edit = QLineEdit()
        input_btn = QPushButton("选择影像文件夹")
        input_btn.clicked.connect(self.select_input_path)

        # 输出路径
        self.output_path_edit = QLineEdit(self.save_path)
        output_btn = QPushButton("选择保存路径")
        output_btn.clicked.connect(self.select_output_path)

        # 提交按钮
        run_btn = QPushButton("开始提取")
        run_btn.clicked.connect(self.run)

        layout.addWidget(QLabel("输入路径："))
        layout.addWidget(self.input_path_edit)
        layout.addWidget(input_btn)
        layout.addWidget(QLabel("保存路径："))
        layout.addWidget(self.output_path_edit)
        layout.addWidget(output_btn)
        layout.addWidget(run_btn)

        self.setLayout(layout)

    def select_input_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择影像文件夹")
        if path:
            self.input_path_edit.setText(path)

    def select_output_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存路径")
        if path:
            self.output_path_edit.setText(path)

    def run(self):
        in_dir = self.input_path_edit.text().strip()
        out_dir = self.output_path_edit.text().strip()

        if in_dir and out_dir:
            self.callback(in_dir, out_dir)
            self.accept()
