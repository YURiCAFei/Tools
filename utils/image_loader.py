import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal
import rasterio
from rasterio.enums import Resampling

class ImageLoadResult(QObject):
    """ 信号结果对象，用于线程完成通知。"""
    finished = pyqtSignal(str, QPixmap)

class ImageLoaderWorker(QRunnable):
    """
    图像加载线程任务（基于QRunnable）。
    支持 GeoTIFF 金字塔自动选择最佳缩放层级以提升加载速度。
    """
    def __init__(self, file_name, transform_container, crs_container, callback):
        super().__init__()
        self.file_name = file_name
        self.transform_container = transform_container
        self.crs_container = crs_container
        self.callback = callback

    def run(self):
        pixmap = ImageLoader.load_image(self.file_name, self.transform_container, self.crs_container)
        self.callback(self.file_name, pixmap)

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

                    # 使用金字塔 overviews 或默认缩放
                    ovr = src.overviews(1)
                    if ovr:
                        decim = ovr[min(len(ovr)-1, 2)]
                        img = src.read(
                            out_shape=(src.count, src.height // decim, src.width // decim),
                            resampling=Resampling.nearest
                        )
                    else:
                        decim = 4  # fallback 缩小比例
                        img = src.read(
                            out_shape=(src.count, src.height // decim, src.width // decim),
                            resampling=Resampling.bilinear
                        )

                    # 格式转换
                    if src.count >= 3:
                        r = ImageLoader.normalize_to_uint8(img[0])
                        g = ImageLoader.normalize_to_uint8(img[1])
                        b = ImageLoader.normalize_to_uint8(img[2])
                        rgb = np.stack([r, g, b], axis=-1)
                    elif src.count == 1:
                        gray = ImageLoader.normalize_to_uint8(img[0])
                        rgb = np.stack([gray] * 3, axis=-1)
                    else:
                        return None

                    h, w, c = rgb.shape
                    qimg = QImage(rgb.tobytes(), w, h, c * w, QImage.Format_RGB888)
                    return QPixmap.fromImage(qimg)
            else:
                return QPixmap(file_name)
        except Exception as e:
            print(f"读取图像失败: {file_name} → {e}")
            return None

    @staticmethod
    def load_async(file_name, transform_container, crs_container, callback):
        """
        异步加载图像，避免卡顿。
        callback: (file_name, QPixmap) 回调
        """
        worker = ImageLoaderWorker(file_name, transform_container, crs_container, callback)
        ImageLoader.thread_pool.start(worker)
