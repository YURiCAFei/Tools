import os.path

from PyQt5.QtWidgets import (
    QDialog, QLabel, QComboBox, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog
)

class LidarDownsampleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("激光点抽稀")
        self.resize(500, 250)
        self.selected_method = "ratio"
        self.init_ui()

        # 自动带入默认工程输出路径（如果设置）
        if parent and hasattr(parent, "project_root") and parent.project_root:
            # self.output_edit.setText(parent.project_root)
            self.output_edit.setText(os.path.join(parent.project_root, "dowmsampled_lidar"))

    def init_ui(self):
        layout = QVBoxLayout()

        # 抽稀方式下拉选择
        method_label = QLabel("抽稀方式:")
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "抽样比例 (ratio)",
            "指定数量 (count)",
            "格网稀疏 (grid)",
            "KMeans聚类 (kmeans)"
        ])
        self.method_combo.currentIndexChanged.connect(self.update_param_field)

        self.param_label = QLabel("抽样比例:")
        self.param_edit = QLineEdit("0.1")

        # 输入路径
        input_label = QLabel("激光数据路径:")
        self.input_edit = QLineEdit()
        input_btn = QPushButton("选择")
        input_btn.clicked.connect(self.choose_input)
        input_row = QHBoxLayout()
        input_row.addWidget(self.input_edit)
        input_row.addWidget(input_btn)

        # 输出路径
        output_label = QLabel("保存路径:")
        self.output_edit = QLineEdit()
        output_btn = QPushButton("选择")
        output_btn.clicked.connect(self.choose_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit)
        output_row.addWidget(output_btn)

        # 输出文件名前缀
        name_label = QLabel("输出文件名前缀:")
        self.name_edit = QLineEdit("downsampled")

        # 按钮
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row = QHBoxLayout()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)

        layout.addWidget(method_label)
        layout.addWidget(self.method_combo)
        layout.addWidget(self.param_label)
        layout.addWidget(self.param_edit)
        layout.addWidget(input_label)
        layout.addLayout(input_row)
        layout.addWidget(output_label)
        layout.addLayout(output_row)
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)
        layout.addLayout(btn_row)
        self.setLayout(layout)

    def update_param_field(self):
        idx = self.method_combo.currentIndex()
        if idx == 0:
            self.param_label.setText("抽样比例 (0~1):")
            self.param_edit.setText("0.1")
            self.selected_method = "ratio"
        elif idx == 1:
            self.param_label.setText("目标点数量:")
            self.param_edit.setText("1000")
            self.selected_method = "count"
        elif idx == 2:
            self.param_label.setText("格网边长（米）:")
            self.param_edit.setText("1.0")
            self.selected_method = "grid"
        elif idx == 3:
            self.param_label.setText("聚类数 (K):")
            self.param_edit.setText("1000")
            self.selected_method = "kmeans"

    def choose_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择激光输入路径")
        if path:
            self.input_edit.setText(path)

    def choose_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存路径")
        if path:
            self.output_edit.setText(path)

    def get_inputs(self):
        return {
            "method": self.selected_method,
            "param": self.param_edit.text().strip(),
            "input_path": self.input_edit.text().strip(),
            "output_path": self.output_edit.text().strip(),
            "filename": self.name_edit.text().strip() or "downsampled"
        }
