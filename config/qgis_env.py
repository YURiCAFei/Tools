from qgis.core import QgsApplication

qgs = None

def init_qgis():
    global qgs
    QgsApplication.setPrefixPath(r"C:\Users\ASUS\anaconda3\envs\lidar-tools\Lib\qgis", True)  # 根据实际修改
    qgs = QgsApplication([], False)
    qgs.initQgis()
