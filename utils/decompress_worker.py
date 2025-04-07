# utils/decompress_worker.py

from PyQt5.QtCore import QThread, pyqtSignal

class DecompressWorker(QThread):
    progress_update = pyqtSignal(str)
    progress_percent = pyqtSignal(float)
    finished = pyqtSignal()
    stopped = pyqtSignal()

    def __init__(self, path, output_dir, decompress_func):
        super().__init__()
        self.path = path
        self.output_dir = output_dir
        self.decompress_func = decompress_func
        self._abort = False

    def stop(self):
        self._abort = True

    def run(self):
        def log(msg):
            self.progress_update.emit(msg)

        def progress(p):
            self.progress_percent.emit(p * 100.0)

        def should_stop():
            return self._abort

        self.decompress_func(
            self.path,
            self.output_dir,
            log_callback=log,
            progress_callback=progress,
            stop_check=should_stop
        )

        if self._abort:
            self.stopped.emit()
        else:
            self.finished.emit()
