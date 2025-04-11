from PyQt5.QtCore import QThread, pyqtSignal
from utils.downsample_logic import process_downsample

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

    def run(self):
        def log(msg):
            self.progress.emit(msg)

        def stop_check():
            return self._abort

        try:
            process_downsample(
                method=self.method,
                param=self.param,
                input_path=self.input_path,
                output_path=self.output_path,
                filename=self.filename,
                log_callback=log,
                stop_check=stop_check
            )
        except Exception as e:
            log(f"❌ 抽稀失败: {e}")

        if self._abort:
            self.stopped.emit()
        else:
            self.finished.emit()

    def stop(self):
        self._abort = True
