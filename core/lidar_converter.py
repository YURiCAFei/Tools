import os
import csv
import glob
from core.thread_pool import ThreadPool

def merge_csv_to_txt(folder_path, output_file):
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    all_points = []

    for csv_file in csv_files:
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            header = next(csv_reader)

            lon_idx = header.index('lon_ph')
            lat_idx = header.index('lat_ph')
            h_idx = header.index('h_ph')
            class_idx = header.index('classification')
            signal_conf_idx = header.index('signal_conf_ph')
            beam_strength_idx = header.index('beam_strength')

            for row in csv_reader:
                if len(row) > max(lon_idx, lat_idx, h_idx, class_idx, signal_conf_idx, beam_strength_idx):
                    if (row[beam_strength_idx] == "strong" and
                        int(row[signal_conf_idx]) > 2 and
                        int(row[class_idx]) == 1):
                        lon = row[lon_idx]
                        lat = row[lat_idx]
                        height = row[h_idx]
                        all_points.append((lat, lon, height))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"{len(all_points)}\n")
        for i, (lat, lon, height) in enumerate(all_points):
            f.write(f"{i+1}\t{lat}\t{lon}\t{height}\n")


def convert_all_lidar_folders(input_dir, output_dir, log_func, logger=None):
    pool = ThreadPool()
    futures = []

    for name in os.listdir(input_dir):
        subdir = os.path.join(input_dir, name)
        if os.path.isdir(subdir):
            output_file = os.path.join(output_dir, f"{name}.txt")
            future = pool.submit(_safe_convert, subdir, output_file, log_func)
            futures.append(future)

    # 等待所有任务完成
    for f in futures:
        f.result()

    log_func("🎉 所有激光格式转换任务已完成")

    if logger:
        logger.flush()


def _safe_convert(subdir, output_file, log_func):
    try:
        merge_csv_to_txt(subdir, output_file)
        log_func(f"✅ 转换完成: {os.path.basename(subdir)} → {output_file}")
    except Exception as e:
        log_func(f"❌ 转换失败: {os.path.basename(subdir)} -> {e}")
