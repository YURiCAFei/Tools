import os
import shutil
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union
import pandas as pd

def get_files(region_shp_path, image_shp_folder, log=print):
    region_gdf = gpd.read_file(region_shp_path)
    region_polygon = region_gdf.unary_union

    all_image_shps = [f for f in os.listdir(image_shp_folder) if f.endswith(".shp")]
    gdfs = []
    for f in all_image_shps:
        try:
            gdf = gpd.read_file(os.path.join(image_shp_folder, f))
            gdf["image_name"] = os.path.join(image_shp_folder, f)
            gdfs.append(gdf)
        except Exception as e:
            log(f"❌ 读取失败: {f} - {e}")
    if not gdfs:
        raise RuntimeError("❌ 未能读取任何有效影像边界文件")
    images_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)
    return region_polygon, images_gdf

def choose_img(region_polygon, images_gdf, result_path, log=print, max_images=99999):
    remaining_area = region_polygon
    connected_region = None
    selected_images = []
    os.makedirs(result_path, exist_ok=True)

    max_allowed = min(max_images, len(images_gdf))
    while len(selected_images) < max_allowed:
        scores = []
        for _, row in images_gdf.iterrows():
            area = row.geometry.area
            intersection = row.geometry.intersection(remaining_area)
            inter_area = intersection.area
            if inter_area == 0:
                continue
            overlap_ratio = inter_area / area
            weight = inter_area * (1 - overlap_ratio)
            if connected_region and not row.geometry.intersects(connected_region):
                continue
            scores.append((weight, row))

        if not scores:
            break
        scores.sort(key=lambda x: -x[0])
        best = scores[0][1]

        selected_images.append(best.image_name)
        images_gdf = images_gdf[images_gdf["image_name"] != best.image_name]
        connected_region = best.geometry if connected_region is None else unary_union([connected_region, best.geometry])
        remaining_area = remaining_area.difference(best.geometry)

        log(f"✅ 选择图像: {os.path.basename(best.image_name)}")

    # 复制对应文件
    copied = []
    for shp in selected_images:
        base = os.path.splitext(shp)[0]
        for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
            src = base + ext
            if os.path.exists(src):
                shutil.copy(src, result_path)
        copied.append(os.path.join(result_path, os.path.basename(shp)))
    return copied  # 返回选中的新路径列表
