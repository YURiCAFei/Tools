import numpy as np
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal
import rasterio
from rasterio.enums import Resampling
import traceback
from PyQt5.QtGui import QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt, QRectF
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString, Point, MultiPoint, base
import geopandas as gpd
from affine import Affine

def convert_gdf_to_pixmap_transform(gdf, pixel_size=1.0):
    try:
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        if gdf.crs.to_epsg() == 4326:
            gdf = gdf.to_crs(epsg=3857)

        gdf = gdf[gdf.geometry.apply(lambda geom: isinstance(geom, base.BaseGeometry))]
        gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notnull()]
        if gdf.empty:
            raise ValueError("没有有效的几何")

        minx, miny, maxx, maxy = gdf.total_bounds
        width = maxx - minx
        height = maxy - miny

        img_width = int(width / pixel_size)
        img_height = int(height / pixel_size)

        pixmap = QPixmap(img_width, img_height)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        pen = QPen(Qt.red)
        pen.setWidth(2)
        painter.setPen(pen)

        def to_local(x, y):
            sx = (x - minx) / pixel_size
            sy = img_height - (y - miny) / pixel_size
            return int(sx), int(sy)

        for geom in gdf.geometry:
            if isinstance(geom, (Polygon, MultiPolygon)):
                polys = [geom] if isinstance(geom, Polygon) else geom.geoms
                for poly in polys:
                    if poly.exterior is None: continue
                    pts = [to_local(x, y) for x, y in poly.exterior.coords]
                    for i in range(len(pts) - 1):
                        painter.drawLine(*pts[i], *pts[i + 1])

            elif isinstance(geom, (LineString, MultiLineString)):
                lines = [geom] if isinstance(geom, LineString) else geom.geoms
                for line in lines:
                    pts = [to_local(x, y) for x, y in line.coords]
                    for i in range(len(pts) - 1):
                        painter.drawLine(*pts[i], *pts[i + 1])

            elif isinstance(geom, (Point, MultiPoint)):
                points = [geom] if isinstance(geom, Point) else geom.geoms
                for pt in points:
                    x, y = to_local(pt.x, pt.y)
                    painter.drawEllipse(x - 2, y - 2, 4, 4)

        painter.end()

        # 输出位置信息
        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2
        transform = Affine.translation(minx, miny) * Affine.scale(pixel_size, -pixel_size)

        return pixmap, transform, center_x, center_y, pixel_size

    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return None, None, None, None, None


class ImageLoadResult(QObject):
    finished = pyqtSignal(str, QPixmap, object)  # 增加 transform 输出

class ImageLoaderWorker(QRunnable):
    def __init__(self, file_name, transform_container, crs_container, callback):
        super().__init__()
        self.file_name = file_name
        self.transform_container = transform_container
        self.crs_container = crs_container
        self.callback = callback

    def run(self):
        pixmap, transform = ImageLoader.load_image(self.file_name, self.transform_container, self.crs_container)
        self.callback(self.file_name, pixmap, transform)

class ImageLoader:
    thread_pool = QThreadPool()

    @staticmethod
    def normalize_to_uint8(arr):
        arr = np.nan_to_num(arr)
        p2, p98 = np.percentile(arr, (2, 98))
        arr = np.clip(arr, p2, p98)
        arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-6) * 255
        return arr.astype(np.uint8)

    @staticmethod
    def load_image(file_name, transform_container, crs_container):
        try:
            if file_name.lower().endswith(('tif', 'tiff')):
                with rasterio.open(file_name, "r") as src:
                    if transform_container[0] is None:
                        transform_container[0] = src.transform
                        crs_container[0] = src.crs

                    transform = src.transform

                    ovr = src.overviews(1)
                    if ovr:
                        decim = ovr[min(len(ovr)-1, 2)]
                        img = src.read(
                            out_shape=(src.count, src.height // decim, src.width // decim),
                            resampling=Resampling.nearest
                        )
                    else:
                        decim = 4
                        img = src.read(
                            out_shape=(src.count, src.height // decim, src.width // decim),
                            resampling=Resampling.bilinear
                        )

                    if src.count >= 3:
                        r = ImageLoader.normalize_to_uint8(img[0])
                        g = ImageLoader.normalize_to_uint8(img[1])
                        b = ImageLoader.normalize_to_uint8(img[2])
                        rgb = np.stack([r, g, b], axis=-1)
                    elif src.count == 1:
                        gray = ImageLoader.normalize_to_uint8(img[0])
                        rgb = np.stack([gray] * 3, axis=-1)
                    else:
                        print(f"[图像加载失败] 通道数不足: {file_name}")
                        return None, None

                    h, w, c = rgb.shape
                    qimg = QImage(rgb.tobytes(), w, h, c * w, QImage.Format_RGB888)
                    return QPixmap.fromImage(qimg), transform
            else:
                return QPixmap(file_name), None
        except Exception as e:
            print(f"[图像加载异常] {file_name}: {str(e)}")
            traceback.print_exc()
            return None, None

    @staticmethod
    def load_async_with_transform(file_name, callback):
        from threading import Thread

        def task():
            pix, trans = ImageLoader.load_image_with_transform(file_name)
            callback(file_name, pix, trans)

        Thread(target=task).start()

    @staticmethod
    def load_image_with_transform(file_name):
        try:
            print(f"[DEBUG] 开始尝试读取图像: {file_name}")
            if file_name.lower().endswith(('tif', 'tiff')):
                with rasterio.open(file_name, "r") as src:
                    transform = src.transform
                    print(f"[DEBUG] transform: {transform}")
                    ovr = src.overviews(1)
                    if ovr:
                        decim = ovr[min(len(ovr) - 1, 2)]
                        img = src.read(
                            out_shape=(src.count, src.height // decim, src.width // decim),
                            resampling=Resampling.nearest
                        )
                    else:
                        decim = 4
                        img = src.read(
                            out_shape=(src.count, src.height // decim, src.width // decim),
                            resampling=Resampling.bilinear
                        )
                    print(f"[DEBUG] rasterio 读取图像成功，shape: {img.shape}")

                    if src.count >= 3:
                        r = ImageLoader.normalize_to_uint8(img[0])
                        g = ImageLoader.normalize_to_uint8(img[1])
                        b = ImageLoader.normalize_to_uint8(img[2])
                        rgb = np.stack([r, g, b], axis=-1)
                    elif src.count == 1:
                        gray = ImageLoader.normalize_to_uint8(img[0])
                        rgb = np.stack([gray] * 3, axis=-1)
                    else:
                        print(f"[图像加载失败] 通道数不足: {file_name}")
                        return None, None

                    h, w, c = rgb.shape
                    qimg = QImage(rgb.tobytes(), w, h, c * w, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    print(f"[DEBUG] 返回 pixmap: {pixmap is not None}, transform: {transform is not None}")
                    return pixmap, transform
            else:
                print(f"[DEBUG] 不是TIFF文件，直接加载 QPixmap: {file_name}")
                return QPixmap(file_name), None
        except Exception as e:
            print(f"[图像加载异常] {file_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None
