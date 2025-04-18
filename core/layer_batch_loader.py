import os
from qgis.core import (
    QgsRasterLayer, QgsVectorLayer, QgsProject
)
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtCore import Qt

def load_layers_batch(layer_paths, canvas, layer_list_widget, log_func):
    valid_layers = []

    for path in layer_paths:
        name = os.path.basename(path)
        if path.lower().endswith((".tif", ".tiff")):
            layer = QgsRasterLayer(path, name)
        elif path.lower().endswith(".shp"):
            layer = QgsVectorLayer(path, name, "ogr")
        else:
            log_func(f"⚠️ 不支持的图层格式，跳过：{path}")
            continue

        if not layer.isValid():
            log_func(f"❌ 图层无效，跳过：{path}")
            continue

        # 为大图构建金字塔
        if isinstance(layer, QgsRasterLayer):
            try:
                if layer.dataProvider().supportsPyramids():
                    result = layer.dataProvider().buildPyramid()
                    if result:
                        log_func(f"📐 金字塔构建成功：{name}")
                    else:
                        log_func(f"⚠️ 金字塔构建失败：{name}")
            except Exception as e:
                log_func(f"⚠️ 金字塔异常：{e}")

        QgsProject.instance().addMapLayer(layer)
        valid_layers.append(layer)

        # 添加到图层列表
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked)
        item.setData(Qt.UserRole, path)
        layer_list_widget.insertItem(0, item)

        log_func(f"🖼 已添加图层：{name}")

    # 统一加载并缩放视图
    if valid_layers:
        canvas.setLayers(valid_layers)
        extent = valid_layers[0].extent()
        for lyr in valid_layers[1:]:
            extent.combineExtentWith(lyr.extent())
        canvas.setExtent(extent)
        canvas.refresh()
        log_func(f"🎯 所有图层加载完成，共 {len(valid_layers)} 个")
