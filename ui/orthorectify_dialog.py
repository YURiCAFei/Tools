import os
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog


class OrthorectifyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("正射影像处理")
        self.resize(500, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 输入影像文件夹
        input_label = QLabel("影像与RPC所在目录：")
        self.input_edit = QLineEdit()
        input_btn = QPushButton("选择")
        input_btn.clicked.connect(self.choose_input)
        input_row = QHBoxLayout()
        input_row.addWidget(self.input_edit)
        input_row.addWidget(input_btn)

        # 输出目录
        output_label = QLabel("保存目录：")
        self.output_edit = QLineEdit()
        output_btn = QPushButton("选择")
        output_btn.clicked.connect(self.choose_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit)
        output_row.addWidget(output_btn)

        # 确定/取消按钮
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row = QHBoxLayout()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)

        # 布局组装
        layout.addWidget(input_label)
        layout.addLayout(input_row)
        layout.addWidget(output_label)
        layout.addLayout(output_row)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def choose_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择影像输入文件夹")
        if path:
            self.input_edit.setText(path)

    def choose_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出保存路径")
        if path:
            self.output_edit.setText(path)

    def get_paths(self):
        return self.input_edit.text().strip(), self.output_edit.text().strip()
