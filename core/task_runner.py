from PyQt5.QtCore import QObject, QThread, pyqtSignal

class TaskRunner(QObject):
    finished = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.func(*self.args, **self.kwargs)
            self.finished.emit()
        except Exception as e:
            self.failed.emit(str(e))
