from PyQt5.QtCore import QObject, QThread, pyqtSignal
from qgis.core import QgsRasterLayer

class LayerLoader(QObject):
    finished = pyqtSignal(object, object, str)  # layer对象, path
    failed = pyqtSignal(str, str)       # path, error message

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            layer = QgsRasterLayer(self.path, self.path.split("/")[-1])
            if not layer.isValid():
                raise Exception("QgsRasterLayer 无效")

            extent = layer.extent()  # 在子线程获取 extent
            self.finished.emit(layer, extent, self.path)
        except Exception as e:
            self.failed.emit(self.path, str(e))