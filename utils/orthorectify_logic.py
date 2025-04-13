import os
import multiprocessing
from osgeo import gdal

gdal.UseExceptions()
MAX_WORKERS = max(1, multiprocessing.cpu_count() // 2)


def process_single_image(image_path, rpc_path, output_dir, log=print, interp_method="bilinear"):
    valid_exts = ('.tif', '.tiff', '.TIF', '.TIFF')
    name = os.path.basename(image_path)
    basename, ext = os.path.splitext(name)
    if ext.lower() not in valid_exts:
        raise ValueError("不支持的影像格式")

    output_path = os.path.join(output_dir, f"{basename}_geo.tif")
    log(f"📥 正在处理影像：{name}")

    resample_mode = gdal.GRA_Bilinear if interp_method == "bilinear" else gdal.GRA_Cubic
    options = gdal.WarpOptions(rpc=True, dstSRS='EPSG:4326', resampleAlg=resample_mode)

    try:
        result = gdal.Warp(destNameOrDestDS=output_path, srcDSOrSrcDSTab=image_path, options=options)
        if result is not None:
            del result  # 强制释放 GDAL 资源
            log(f"✅ 生成成功：{os.path.basename(output_path)}")
        else:
            raise RuntimeError("GDAL Warp 返回 None")
    except Exception as e:
        log(f"❌ 正射失败：{name} - {str(e)}")
        raise

    return output_path
