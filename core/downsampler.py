import os
from math import floor
import random
from core.thread_pool import ThreadPool

def downsample_all(input_dir, output_dir, target_count, log_func, logger=None):
    pool = ThreadPool()
    futures = []

    for file in os.listdir(input_dir):
        if not file.endswith(".txt"):
            continue
        input_path = os.path.join(input_dir, file)
        output_path = os.path.join(output_dir, file)
        futures.append(pool.submit(_downsample_uniform, input_path, output_path, target_count, log_func))

    for f in futures:
        f.result()

    log_func("🎯 点云抽稀全部完成")
    if logger:
        logger.flush()


def _downsample_uniform(input_file, output_file, target_count, log_func):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_count = int(lines[0].strip())
        point_lines = lines[1:]

        points = []
        for line in point_lines:
            parts = line.strip().split()
            if len(parts) >= 4:
                lat, lon = float(parts[1]), float(parts[2])
                points.append((lat, lon, line.rstrip('\n')))  # 保留原始行

        if len(points) <= target_count:
            # 不抽稀，直接复制，保留原格式
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"{len(points)}\n")
                f.writelines(line + "\n" for _, _, line in points)
            log_func(f"⚠️ 点数不足，未抽稀: {os.path.basename(input_file)} → 原始点数 {len(points)}")
            return

        # 均匀抽稀（网格采样）
        lats = [p[0] for p in points]
        lons = [p[1] for p in points]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        grid_size = max(1, int((len(points) ** 0.5) / 5))
        grid = dict()
        for lat, lon, line in points:
            i = floor((lat - min_lat) / (max_lat - min_lat + 1e-8) * grid_size)
            j = floor((lon - min_lon) / (max_lon - min_lon + 1e-8) * grid_size)
            key = (i, j)
            grid.setdefault(key, []).append(line)

        selected_lines = [random.choice(pts) for pts in grid.values()]
        if len(selected_lines) > target_count:
            selected_lines = random.sample(selected_lines, target_count)

        # 写入文件，保持原行格式
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"{len(selected_lines)}\n")
            f.writelines(line + "\n" if not line.endswith("\n") else line for line in selected_lines)

        log_func(f"✅ 抽稀完成: {os.path.basename(input_file)} → {len(selected_lines)} 点")
    except Exception as e:
        log_func(f"❌ 抽稀失败: {os.path.basename(input_file)} → {e}")
