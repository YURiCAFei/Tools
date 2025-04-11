# utils/satmap2gp_worker.py

from PyQt5.QtCore import QThread, pyqtSignal
from utils.Satmap2GPlidar import merge_csv_to_txt

class Satmap2GPWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, lidar_path, save_path, file_name):
        super().__init__()
        self.lidar_path = lidar_path
        self.save_path = save_path
        self.file_name = file_name

    def run(self):
        output_file = f"{self.save_path}/{self.file_name}.txt"
        merge_csv_to_txt(self.lidar_path, output_file, log_callback=self.progress.emit)
        self.finished.emit()
