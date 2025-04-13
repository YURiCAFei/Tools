import os
from PyQt5.QtCore import QThread, pyqtSignal
from utils.orthorectify_logic import process_single_image


class OrthoRectifyWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)  # 文件名, 输出路径

    def __init__(self, image_path, rpc_path, output_path):
        super().__init__()
        self.image_path = image_path
        self.rpc_path = rpc_path
        self.output_path = output_path

    def run(self):
        try:
            result_path = process_single_image(
                self.image_path, self.rpc_path, self.output_path, log=self.progress.emit
            )
            self.finished.emit(self.image_path, result_path)
        except Exception as e:
            self.progress.emit(f"❌ 处理失败：{self.image_path} ({e})")
