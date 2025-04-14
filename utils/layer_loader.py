import os
import geopandas as gpd
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QListWidgetItem, QGraphicsTextItem
from PyQt5.QtCore import Qt
from utils.image_loader import convert_gdf_to_pixmap_transform

def load_shapefile(shp_path, canvas_widget, list_widget, log=None):
    try:
        if not shp_path.lower().endswith(".shp"):
            if log:
                log(f"⏭️ 跳过非 SHP 文件: {shp_path}")
            return

        # ✅ 提示文字显示
        text_item = QGraphicsTextItem("请到 ENVI、QGIS 查看 SHP")
        font = QFont("Arial", 24)
        font.setBold(True)
        text_item.setFont(font)
        text_item.setDefaultTextColor(Qt.darkRed)
        text_item.setPos(100, 100)
        canvas_widget.scene.addItem(text_item)

        # ✅ 清理旧图层（可选）
        # canvas_widget.scene.clear()  # 如需清屏再取消注释

        name = os.path.splitext(os.path.basename(shp_path))[0]
        item = QListWidgetItem(name)
        item.setCheckState(Qt.Checked)
        list_widget.addItem(item)

        if log:
            log(f"📄 已加载 SHP 名称：{name}（仅用于标记，不显示）")

    except Exception as e:
        if log:
            log(f"❌ 加载失败: {shp_path} - {e}")
        else:
            print(f"❌ 加载 SHP 文件失败: {shp_path}, 错误: {e}")

