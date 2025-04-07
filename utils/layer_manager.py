from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

class LayerManager:
    def __init__(self, list_widget, render_callback):
        """
        构造图层管理器。

        参数：
            list_widget: QListWidget 控件，显示图层名和勾选框。
            render_callback: 图层更新时的回调函数。
        """
        self.list_widget = list_widget
        self.render_callback = render_callback
        self.layers = {}  # 图层名 -> QPixmap

        # 当图层勾选状态变化时，立即触发渲染刷新
        self.list_widget.itemChanged.connect(self.render_callback)

    def add_layer(self, name, pixmap):
        """
        添加图层，并将其作为可勾选项插入列表。

        参数：
            name: 图层名（如文件名）
            pixmap: 图像 QPixmap
        """
        self.layers[name] = pixmap
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked)
        self.list_widget.addItem(item)
        self.render_callback()

    def get_checked_layers(self):
        """
        获取所有勾选状态为选中的图层。

        返回：
            List[QPixmap]
        """
        return [self.layers[self.list_widget.item(i).text()]
                for i in range(self.list_widget.count())
                if self.list_widget.item(i).checkState() == Qt.Checked]

    def render_combined(self):
        """
        将所有勾选图层进行叠加合成。

        返回：
            QPixmap 或 None
        """
        checked = self.get_checked_layers()
        if not checked:
            return None

        base = checked[0].copy()
        painter = QPainter(base)
        for layer in checked[1:]:
            painter.setOpacity(0.5)
            painter.drawPixmap(0, 0, layer)
        painter.end()
        return base

    def is_layer_active(self, name):
        """
        判断指定图层是否处于勾选状态。

        参数：
            name: 图层名（str）

        返回：
            bool: True 表示被勾选，False 表示未勾选
        """
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() == name:
                return item.checkState() == Qt.Checked
        return False
