import os
import glob
from osgeo import gdal
from core.thread_pool import ThreadPool

gdal.UseExceptions()

def find_rpc_file(image_path, input_folder):
    name = os.path.splitext(os.path.basename(image_path))[0]
    candidates = [
        os.path.join(input_folder, f"{name}_rpc.txt"),
        os.path.join(input_folder, f"{name}.rpb"),
        os.path.join(input_folder, f"{name}.RPB")
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def is_valid_image(file):
    return file.lower().endswith(('.tif', '.tiff'))

def orthorectify_all(input_folder, output_folder, log_func):
    tif_files = [
        os.path.join(input_folder, f)
        for f in os.listdir(input_folder)
        if is_valid_image(f) and os.path.isfile(os.path.join(input_folder, f))
    ]
    pool = ThreadPool()
    futures = []

    for tif_path in tif_files:
        rpc_path = find_rpc_file(tif_path, input_folder)
        if not rpc_path:
            log_func(f"⚠️ 未找到 RPC 文件: {os.path.basename(tif_path)}")
            continue

        output_path = os.path.join(output_folder, os.path.basename(tif_path))
        futures.append(pool.submit(_orthorectify_one, tif_path, rpc_path, output_path, log_func))

    for f in futures:
        f.result()

    return [os.path.join(output_folder, os.path.basename(p)) for p in tif_files if os.path.exists(os.path.join(output_folder, os.path.basename(p)))]

def _orthorectify_one(tif_path, rpc_path, output_path, log_func):
    try:
        gdal.SetConfigOption("RPC_FILE", rpc_path)
        warp_options = gdal.WarpOptions(
            format="GTiff",
            rpc=True,
            resampleAlg=gdal.GRA_Cubic,
            multithread=True,
            creationOptions=["TILED=YES", "COMPRESS=DEFLATE"]
        )
        gdal.Warp(output_path, tif_path, options=warp_options)
        log_func(f"✅ 正射完成: {os.path.basename(tif_path)}")
    except Exception as e:
        log_func(f"❌ 正射失败: {os.path.basename(tif_path)} → {e}")
