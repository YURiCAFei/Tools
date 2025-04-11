import os
import csv
import glob

def merge_csv_to_txt(folder_path, output_file, log_callback=print):
    # import os
    # import csv
    # import glob

    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not csv_files:
        log_callback(f"⚠️ 未在目录中找到 CSV 文件：{folder_path}")
        return

    all_points = []

    for csv_file in csv_files:
        point_count = 0
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            try:
                header = next(csv_reader)
                lon_idx = header.index('lon_ph')
                lat_idx = header.index('lat_ph')
                h_idx = header.index('h_ph')
                class_idx = header.index('classification')
                signal_conf_idx = header.index('signal_conf_ph')
                beam_strength_idx = header.index('beam_strength')
            except Exception as e:
                log_callback(f"⚠️ 字段缺失，跳过：{os.path.basename(csv_file)} ({e})")
                continue

            for row in csv_reader:
                try:
                    if len(row) <= max(lon_idx, lat_idx, h_idx, class_idx, signal_conf_idx, beam_strength_idx):
                        continue

                    beam = row[beam_strength_idx].strip().lower()
                    signal_conf = int(row[signal_conf_idx])
                    classification = int(row[class_idx])

                    if beam == "strong" and signal_conf > 2 and classification == 1:
                        lon = row[lon_idx]
                        lat = row[lat_idx]
                        height = row[h_idx]
                        all_points.append((lat, lon, height))
                        point_count += 1
                except:
                    continue

        log_callback(f"📄 已处理：{os.path.basename(csv_file)}（符合条件点数: {point_count}）")

    if not all_points:
        log_callback("⚠️ 所有点被过滤或未匹配，未写入任何数据。")
        return

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"{len(all_points)}\n")
        for i, (lat, lon, height) in enumerate(all_points):
            f.write(f"{i+1}\t{lat}\t{lon}\t{height}\n")

    log_callback(f"✅ 合并完成：{len(csv_files)} 个 CSV，共导出 {len(all_points)} 个点 → {output_file}")
