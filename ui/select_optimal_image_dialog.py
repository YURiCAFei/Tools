from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QSpinBox
)
import os

class SelectOptimalImageDialog(QDialog):
    def __init__(self, default_output_path, callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle("优选图像子集")
        self.callback = callback
        self.default_output_path = default_output_path

        layout = QVBoxLayout()

        # 目标区域 SHP
        self.shp_edit = QLineEdit()
        shp_btn = QPushButton("选择区域 shp")
        shp_btn.clicked.connect(self.select_shp)
        row1 = QHBoxLayout()
        row1.addWidget(self.shp_edit)
        row1.addWidget(shp_btn)

        # 图像边界目录
        self.image_dir_edit = QLineEdit()
        image_btn = QPushButton("选择图像边界目录")
        image_btn.clicked.connect(self.select_image_dir)
        row2 = QHBoxLayout()
        row2.addWidget(self.image_dir_edit)
        row2.addWidget(image_btn)

        # 输出路径
        self.output_edit = QLineEdit(self.default_output_path)
        output_btn = QPushButton("选择保存目录")
        output_btn.clicked.connect(self.select_output_dir)
        row3 = QHBoxLayout()
        row3.addWidget(self.output_edit)
        row3.addWidget(output_btn)

        # 最大图像数
        row4 = QHBoxLayout()
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 99999)
        self.max_spin.setValue(99999)
        row4.addWidget(QLabel("最大图像数量："))
        row4.addWidget(self.max_spin)

        # 按钮区
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        row5 = QHBoxLayout()
        row5.addWidget(ok_btn)
        row5.addWidget(cancel_btn)

        layout.addWidget(QLabel("目标区域边界 SHP："))
        layout.addLayout(row1)
        layout.addWidget(QLabel("图像边界目录："))
        layout.addLayout(row2)
        layout.addWidget(QLabel("输出路径："))
        layout.addLayout(row3)
        layout.addLayout(row4)
        layout.addLayout(row5)
        self.setLayout(layout)

    def select_shp(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择目标区域 SHP", "", "Shapefiles (*.shp)")
        if path:
            self.shp_edit.setText(path)

    def select_image_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择图像边界目录")
        if path:
            self.image_dir_edit.setText(path)

    def select_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存路径")
        if path:
            self.output_edit.setText(path)

    def get_inputs(self):
        return (
            self.shp_edit.text().strip(),
            self.image_dir_edit.text().strip(),
            self.output_edit.text().strip(),
            self.max_spin.value()
        )
