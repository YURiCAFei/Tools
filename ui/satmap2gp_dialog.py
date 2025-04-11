from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog
)

class Satmap2GPDialog(QDialog):
    """
    激光格式转换：Satmap2GP 模式对话框
    输入：
    - 激光源路径（文件夹）
    - 保存路径（文件夹）
    - 输出文件名（不含扩展名）
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("激光格式转换 - Satmap2GP")
        self.resize(500, 200)

        self.lidar_dir = ""
        self.save_dir = ""
        self.filename = "lidar"

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 激光数据路径
        lidar_label = QLabel("激光路径（文件夹）:")
        self.lidar_edit = QLineEdit()
        lidar_browse = QPushButton("选择")
        lidar_browse.clicked.connect(self.select_lidar_dir)
        lidar_row = QHBoxLayout()
        lidar_row.addWidget(self.lidar_edit)
        lidar_row.addWidget(lidar_browse)

        # 保存路径
        save_label = QLabel("保存路径（文件夹）:")
        self.save_edit = QLineEdit()
        save_browse = QPushButton("选择")
        save_browse.clicked.connect(self.select_save_dir)
        save_row = QHBoxLayout()
        save_row.addWidget(self.save_edit)
        save_row.addWidget(save_browse)

        # 输出文件名
        name_label = QLabel("输出文件名（默认 lidar）:")
        self.name_edit = QLineEdit("lidar")

        # 按钮行
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn.clicked.connect(self.reject)
        btn_row = QHBoxLayout()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)

        layout.addWidget(lidar_label)
        layout.addLayout(lidar_row)
        layout.addWidget(save_label)
        layout.addLayout(save_row)
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def select_lidar_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择激光路径")
        if path:
            self.lidar_edit.setText(path)

    def select_save_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存路径")
        if path:
            self.save_edit.setText(path)

    def on_ok(self):
        self.lidar_dir = self.lidar_edit.text().strip()
        self.save_dir = self.save_edit.text().strip()
        self.filename = self.name_edit.text().strip() or "lidar"
        self.accept()

    def get_inputs(self):
        """返回 (激光路径, 保存路径, 文件名) 三元组"""
        return self.lidar_dir, self.save_dir, self.filename
