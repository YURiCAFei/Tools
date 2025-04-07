from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog
)

class DecompressDialog(QDialog):
    """
    解压设置对话框，提供以下路径输入项：
    1. 压缩文件路径（可选）
    2. 压缩文件夹路径（可选）
    3. 解压保存路径（必填）

    用户需选择文件或文件夹中的任意一个。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("解压设置")
        self.resize(500, 200)

        self.file_path = ""
        self.folder_path = ""
        self.output_path = ""

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 第一行：压缩文件
        file_label = QLabel("压缩文件路径（优先使用，zip/rar/7z 等）：")
        self.file_edit = QLineEdit()
        file_browse = QPushButton("选择")
        file_browse.clicked.connect(self.select_file)
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_edit)
        file_row.addWidget(file_browse)

        # 第二行：压缩文件夹
        folder_label = QLabel("压缩文件夹路径（若未填写文件路径）：")
        self.folder_edit = QLineEdit()
        folder_browse = QPushButton("选择")
        folder_browse.clicked.connect(self.select_folder)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder_edit)
        folder_row.addWidget(folder_browse)

        # 第三行：输出路径
        out_label = QLabel("解压保存路径（必填）：")
        self.out_edit = QLineEdit()
        out_browse = QPushButton("选择")
        out_browse.clicked.connect(self.select_output)
        out_row = QHBoxLayout()
        out_row.addWidget(self.out_edit)
        out_row.addWidget(out_browse)

        # 确定/取消按钮
        btn_ok = QPushButton("确定")
        btn_cancel = QPushButton("取消")
        btn_ok.clicked.connect(self.on_ok)
        btn_cancel.clicked.connect(self.reject)
        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)

        # 添加组件到主布局
        layout.addWidget(file_label)
        layout.addLayout(file_row)
        layout.addWidget(folder_label)
        layout.addLayout(folder_row)
        layout.addWidget(out_label)
        layout.addLayout(out_row)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择压缩文件")
        if path:
            self.file_edit.setText(path)

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "选择压缩文件夹")
        if path:
            self.folder_edit.setText(path)

    def select_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择解压输出路径")
        if path:
            self.out_edit.setText(path)

    def on_ok(self):
        self.file_path = self.file_edit.text().strip()
        self.folder_path = self.folder_edit.text().strip()
        self.output_path = self.out_edit.text().strip()
        self.accept()

    def get_paths(self):
        """
        返回用户输入的路径三元组：
        (file_path, folder_path, output_path)
        """
        return self.file_path, self.folder_path, self.output_path
