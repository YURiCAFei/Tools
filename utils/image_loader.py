import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal
import rasterio
from rasterio.enums import Resampling
import traceback
import threading

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
