from PyQt5.QtCore import QThread, pyqtSignal
import os
from utils.downsample_logic import process_downsample_single_file


class SingleFileDownsampleWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, file_path, method, param, output_dir, filename):
        super().__init__()
        self.file_path = file_path
        self.method = method
        self.param = param
        self.output_dir = output_dir
        self.filename = filename
        self._abort = False

    def stop(self):
        self._abort = True

    def run(self):
        def log(msg):
            self.progress.emit(f"[{os.path.basename(self.file_path)}] {msg}")

        def stop_check():
            return self._abort

        try:
            process_downsample_single_file(
                self.file_path, self.method, self.param,
                self.output_dir, self.filename,
                log_callback=log,
                stop_check=stop_check
            )
        except Exception as e:
            log(f"❌ 异常终止: {e}")

        self.finished.emit(self.file_path)


class DownsampleWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    stopped = pyqtSignal()

    def __init__(self, input_path, output_path, method, param, filename):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.method = method
        self.param = param
        self.filename = filename
        self._abort = False
        self.threads = []
        self.finished_files = 0
        self.total_files = 0

    def run(self):
        self.finished_files = 0
        self.threads = []

        input_files = [
            os.path.join(self.input_path, f)
            for f in os.listdir(self.input_path)
            if f.endswith((".csv", ".txt"))
        ]
        self.total_files = len(input_files)

        if not input_files:
            self.progress.emit("❌ 无有效输入文件")
            self.finished.emit()
            return

        for fpath in input_files:
            thread = SingleFileDownsampleWorker(
                fpath, self.method, self.param,
                self.output_path, self.filename
            )
            thread.progress.connect(self.progress.emit)
            thread.finished.connect(self.on_file_finished)
            thread.start()
            self.threads.append(thread)

    def on_file_finished(self, fpath):
        self.finished_files += 1
        self.progress.emit(f"📦 文件处理完成：{os.path.basename(fpath)}")

        if self.finished_files == self.total_files:
            self.progress.emit("🎉 所有文件处理完成")
            self.finished.emit()

    def stop(self):
        self._abort = True
        for thread in getattr(self, "threads", []):
            thread.stop()
