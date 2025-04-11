from PyQt5.QtCore import QThread, pyqtSignal

class DecompressWorker(QThread):
    progress_update = pyqtSignal(str)
    finished = pyqtSignal()
    stopped = pyqtSignal()

    def __init__(self, input_path, output_path, decompress_func):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.decompress_func = decompress_func
        self._abort = False

    def run(self):
        def log(msg):
            self.progress_update.emit(msg)

        def stop_check():
            return self._abort

        self.decompress_func(
            self.input_path,
            self.output_path,
            log_callback=log,
            stop_check=stop_check
        )
        if self._abort:
            self.stopped.emit()
        else:
            self.finished.emit()

    def stop(self):
        self._abort = True
