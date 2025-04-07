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
    def load_image(file_name, transform_container, crs_container):
        """
        加载图像并返回 QPixmap 对象（用于主线程或线程任务中）。

        参数：
            file_name: 文件路径
            transform_container: 用于传递 transform（仿射矩阵）
            crs_container: 用于传递 crs（坐标系统）

        返回：
            QPixmap 或 None（加载失败）
        """
        try:
            if file_name.lower().endswith(('tif', 'tiff')):
                with rasterio.open(file_name, "r") as src:
                    if transform_container[0] is None:
                        transform_container[0] = src.transform
                        crs_container[0] = src.crs

                    ovr = src.overviews(1)
                    if ovr:
                        decim = ovr[min(len(ovr)-1, 2)]
                        img = src.read(
                            out_dtype='uint8',
                            out_shape=(src.count, src.height // decim, src.width // decim),
                            resampling=Resampling.nearest
                        )
                    else:
                        img = src.read(out_dtype='uint8', resampling=Resampling.bilinear)

                    if src.count >= 3:
                        img = img[:3].transpose(1, 2, 0)
                    elif src.count == 1:
                        band = img[0]
                        img = np.stack((band,) * 3, axis=-1)
                    else:
                        return None

                    h, w, c = img.shape
                    qimg = QImage(img.tobytes(), w, h, c * w, QImage.Format_RGB888)
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
