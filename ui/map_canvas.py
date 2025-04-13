from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtCore import Qt, QPointF, QEvent
from PyQt5.QtGui import QPixmap, QWheelEvent, QPainter, QKeyEvent
import rasterio.transform

class MapCoordinateTransformer:
    def __init__(self, base_transform):
        self.transform = base_transform  # rasterio.Affine 仿射矩阵

    def geo_to_scene(self, lon, lat):
        col, row = ~self.transform * (lon, lat)
        return QPointF(col, row)

    def scene_to_geo(self, x, y):
        lon, lat = self.transform * (x, y)
        return lon, lat

class MapViewWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.layers = {}
        self.layer_offsets = {}  # 图层平移偏移
        self.active_layer = None  # 当前选中的需要平移的图层
        self.transformer = None
        self.setMouseTracking(True)
        self.coord_label = None  # 外部注入坐标显示 QLabel
        self.scale_factor = 1.15
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def set_base_transform(self, transform):
        self.transformer = MapCoordinateTransformer(transform)

    def set_active_layer(self, name):
        self.active_layer = name

    def add_layer(self, name, pixmap: QPixmap, transform):
        if self.transformer is None:
            self.set_base_transform(transform)

        pixel_size = abs(transform.a)
        if not hasattr(self, 'base_pixel_size'):
            self.base_pixel_size = pixel_size

        scale_ratio = pixel_size / self.base_pixel_size

        center_lon = transform.c + transform.a * (pixmap.width() / 2 - 0.5)
        center_lat = transform.f + transform.e * (pixmap.height() / 2 - 0.5)
        center_scene = self.transformer.geo_to_scene(center_lon, center_lat)

        item = QGraphicsPixmapItem(pixmap)
        item.setOffset(-pixmap.width() / 2, -pixmap.height() / 2)
        item.setPos(center_scene)
        item.setScale(scale_ratio)

        self.scene.addItem(item)
        self.layers[name] = item
        self.layer_offsets[name] = QPointF(0, 0)

    def apply_offset(self, name):
        if name in self.layers and name in self.layer_offsets:
            item = self.layers[name]
            base_pos = item.pos()
            offset = self.layer_offsets[name]
            item.setPos(base_pos + offset)

    def adjust_active_layer(self, dx=0.0, dy=0.0):
        if self.active_layer and self.active_layer in self.layer_offsets:
            self.layer_offsets[self.active_layer] += QPointF(dx, dy)
            self.apply_offset(self.active_layer)

    def keyPressEvent(self, event: QKeyEvent):
        if self.active_layer:
            step = 0.1 if event.modifiers() & Qt.ControlModifier else 1.0
            if event.key() == Qt.Key_Up:
                self.adjust_active_layer(0, -step)
            elif event.key() == Qt.Key_Down:
                self.adjust_active_layer(0, step)
            elif event.key() == Qt.Key_Left:
                self.adjust_active_layer(-step, 0)
            elif event.key() == Qt.Key_Right:
                self.adjust_active_layer(step, 0)
        else:
            super().keyPressEvent(event)

    def remove_layer(self, name):
        if name in self.layers:
            self.scene.removeItem(self.layers[name])
            del self.layers[name]
            del self.layer_offsets[name]

    def set_layer_visible(self, name, visible):
        if name in self.layers:
            self.layers[name].setVisible(visible)

    def mouseMoveEvent(self, event):
        if self.transformer and self.coord_label:
            scene_pos = self.mapToScene(event.pos())
            lon, lat = self.transformer.scene_to_geo(scene_pos.x(), scene_pos.y())
            self.coord_label.setText(f"坐标: {lon:.6f}, {lat:.6f}")
        super().mouseMoveEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        zoom_in = event.angleDelta().y() > 0
        factor = self.scale_factor if zoom_in else 1 / self.scale_factor
        self.scale(factor, factor)

    def clear_layers(self):
        for item in self.layers.values():
            self.scene.removeItem(item)
        self.layers.clear()
        self.layer_offsets.clear()

    def center_on_layer(self, name):
        if name in self.layers:
            self.centerOn(self.layers[name])
