import os
import csv
import random
import numpy as np
from sklearn.cluster import KMeans

def load_points_from_csv(path):
    points = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        lat_idx = header.index("lat_ph")
        lon_idx = header.index("lon_ph")
        h_idx = header.index("h_ph")
        for row in reader:
            try:
                lat = float(row[lat_idx])
                lon = float(row[lon_idx])
                h = float(row[h_idx])
                points.append((lat, lon, h))
            except:
                continue
    return points, "csv"

def load_points_from_txt(path):
    points = []
    with open(path, 'r', encoding='utf-8') as f:
        count = int(f.readline().strip())
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                lat, lon, h = float(parts[1]), float(parts[2]), float(parts[3])
                points.append((lat, lon, h))
    return points, "txt"

def save_points_to_txt(points, output_path, log_callback=None, stop_check=None):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"{len(points)}\n")
        for i, p in enumerate(points):
            if stop_check and stop_check():
                log_callback("🟥 中止写入 .txt")
                return
            f.write(f"{i+1}\t{p[0]}\t{p[1]}\t{p[2]}\n")
            if log_callback:
                log_callback(f"✏️ 写入点 {i+1}: {p[0]:.6f}, {p[1]:.6f}, {p[2]:.2f}")
                if (i + 1) % 1000 == 0:
                    log_callback(f"📌 已写入 {i+1} 个点...")

def save_points_to_csv(points, output_path, log_callback=None, stop_check=None):
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['lat_ph', 'lon_ph', 'h_ph'])
        for i, p in enumerate(points):
            if stop_check and stop_check():
                log_callback("🟥 中止写入 .csv")
                return
            writer.writerow(p)
            if log_callback:
                log_callback(f"✏️ 写入点 {i+1}: {p[0]:.6f}, {p[1]:.6f}, {p[2]:.2f}")
                if (i + 1) % 1000 == 0:
                    log_callback(f"📌 已写入 {i+1} 个点...")

def downsample_by_ratio(points, ratio):
    k = int(len(points) * ratio)
    return random.sample(points, k)

def downsample_by_count(points, count):
    import numpy as np
    count = min(count, len(points))
    indices = np.linspace(0, len(points) - 1, num=count, dtype=int)
    return [points[i] for i in indices]

def downsample_by_grid(points, grid_size):
    from collections import defaultdict
    seen = {}
    for p in points:
        key = (int(p[0] / grid_size), int(p[1] / grid_size))
        if key not in seen:
            seen[key] = p
    return list(seen.values())

def downsample_by_kmeans(points, k):
    if len(points) <= k:
        return points
    k = min(k, len(points))
    coords = np.array([[p[0], p[1]] for p in points])
    kmeans = KMeans(n_clusters=k, algorithm='elkan', random_state=42, n_init='auto')
    kmeans.fit(coords)
    centers = kmeans.cluster_centers_
    result = []
    for c in centers:
        dists = np.linalg.norm(coords - c, axis=1)
        idx = np.argmin(dists)
        result.append(points[idx])
    return result

def process_downsample(method, param, input_path, output_path, filename,
                       log_callback=print, stop_check=None):
    all_points = []
    input_files = [f for f in os.listdir(input_path) if f.endswith((".csv", ".txt"))]

    if not input_files:
        log_callback("❌ 输入目录下无有效 .csv 或 .txt 文件")
        return

    for file in input_files:
        if stop_check and stop_check():
            log_callback("🟥 抽稀中断（在文件级别）")
            return

        full_path = os.path.join(input_path, file)
        log_callback(f"📥 正在读取: {file}")

        if file.endswith(".csv"):
            points, fmt = load_points_from_csv(full_path)
        else:
            points, fmt = load_points_from_txt(full_path)

        if not points:
            log_callback(f"⚠️ 文件 {file} 无有效点，跳过")
            continue

        try:
            if method == "ratio":
                subset = downsample_by_ratio(points, float(param))
            elif method == "count":
                subset = downsample_by_count(points, int(param))
            elif method == "grid":
                subset = downsample_by_grid(points, float(param))
            elif method == "kmeans":
                subset = downsample_by_kmeans(points, int(param))
            else:
                log_callback(f"❌ 不支持的抽样方法: {method}")
                continue
        except Exception as e:
            log_callback(f"❌ 抽样失败: {file} ({e})")
            continue

        if stop_check and stop_check():
            log_callback("🟥 抽稀中断（在写入前）")
            return

        output_file = os.path.join(output_path, filename + "_" + os.path.splitext(file)[0] + "." + fmt)
        if fmt == "csv":
            save_points_to_csv(subset, output_file, log_callback, stop_check)
        else:
            save_points_to_txt(subset, output_file, log_callback, stop_check)

        log_callback(f"✅ 完成: {file} → {os.path.basename(output_file)} ({len(subset)} 点)")
