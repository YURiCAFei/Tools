from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QTransform, QPixmap
from PyQt5.QtCore import Qt
import numpy as np
from PyQt5.QtGui import QPainter

class MapViewWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(self.renderHints() |
                            QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.layer_items = {}
        self.scale_factor = 1.0

    def add_layer(self, name, pixmap: QPixmap, transform):
        """
        添加图层到地图显示窗口中。

        参数：
            name: 图层名称
            pixmap: QPixmap 对象
            transform: rasterio 的仿射 transform 对象
        """
        # 仿射变换左上角坐标
        left = transform.c
        top = transform.f
        res_x = transform.a
        res_y = -transform.e  # 注意 y 方向是负的

        # 假设图像像素大小是原始尺寸
        width = pixmap.width()
        height = pixmap.height()

        # 将地理坐标转换为像素坐标（缩放视图坐标系）
        x = left / res_x
        y = top / res_y

        item = QGraphicsPixmapItem(pixmap)
        item.setOffset(x, y)
        item.setZValue(len(self.layer_items))
        self.scene.addItem(item)
        self.layer_items[name] = item

    def clear_layers(self):
        self.scene.clear()
        self.layer_items.clear()

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            factor = zoom_in_factor
        else:
            factor = zoom_out_factor
        self.scale(factor, factor)
        self.scale_factor *= factor

    def reset_view(self):
        self.resetTransform()
        self.scale_factor = 1.0
