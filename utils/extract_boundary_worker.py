import os
from osgeo import gdal
from shapely.geometry import Polygon
import geopandas as gpd
from PyQt5.QtCore import QRunnable, pyqtSignal, QObject

class ExtractWorkerSignals(QObject):
    finished = pyqtSignal(str)

class ExtractBoundaryTask(QRunnable):
    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path  # full path to .shp file (without extension change)
        self.signals = ExtractWorkerSignals()

    def run(self):
        try:
            tif_path = self.input_path

            ds = gdal.Open(tif_path)
            rpc = ds.GetMetadata('RPC')
            if not rpc or 'LINE_OFF' not in rpc:
                self.signals.finished.emit(f"⚠️ 未识别 RPC 信息: {os.path.basename(tif_path)}")
                return

            cols = ds.RasterXSize
            rows = ds.RasterYSize

            transformer = gdal.Transformer(ds, None, ['METHOD=RPC'])
            if not transformer:
                self.signals.finished.emit(f"❌ Transformer 构建失败: {os.path.basename(tif_path)}")
                return

            pixel_corners = [(0, 0), (cols, 0), (cols, rows), (0, rows)]
            geo_corners = []

            for x, y in pixel_corners:
                success, point = transformer.TransformPoint(False, x, y)
                if not success:
                    raise RuntimeError(f"RPC 变换失败: ({x}, {y})")
                geo_corners.append((point[0], point[1]))

            polygon = Polygon(geo_corners)
            gdf = gpd.GeoDataFrame({'geometry': [polygon]}, crs="EPSG:4326")
            gdf.to_file(self.output_path, driver='ESRI Shapefile')

            self.signals.finished.emit(f"✅ 成功输出: {os.path.basename(self.output_path)}")

        except Exception as e:
            self.signals.finished.emit(f"❌ 处理失败 {os.path.basename(self.input_path)}: {e}")
