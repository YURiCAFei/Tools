from rasterio.transform import xy
from rasterio.warp import transform as warp_transform  # 避免与 Affine 冲突

class CoordConverter:
    @staticmethod
    def to_wgs84(transform, crs, x, y):
        """
        将图像像素坐标 (x, y) 转换为 WGS84 经纬度坐标。

        参数：
            transform: Affine 仿射变换矩阵
            crs: 当前影像的坐标系统（rasterio.crs）
            x: 图像坐标系中的 x 像素位置（列）
            y: 图像坐标系中的 y 像素位置（行）

        返回：
            (lon, lat)：对应的 WGS84 坐标（EPSG:4326）
        """
        lon, lat = xy(transform, y, x)
        lon_wgs84, lat_wgs84 = warp_transform(crs, 'EPSG:4326', [lon], [lat])
        return lon_wgs84[0], lat_wgs84[0]