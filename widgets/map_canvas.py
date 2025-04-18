from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
from qgis.gui import QgsMapCanvas
from qgis.core import QgsProject


class MapCanvas(QgsMapCanvas):
    coordinatesChanged = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCanvasColor(QColor("white"))
        self.setRenderFlag(True)
        self.xyCoordinates.connect(self._on_mouse_move)
        QgsProject.instance().clear()

    def _on_mouse_move(self, point):
        self.coordinatesChanged.emit(point.x(), point.y())
