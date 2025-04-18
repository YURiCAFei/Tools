import os
import shutil
import zipfile
import tarfile
import rarfile  # 需要 pip install rarfile
from core.thread_pool import ThreadPool


def unpack_all(input_folder, output_folder, log_func=print):
    supported_ext = (".zip", ".tar", ".gz", ".bz2", ".xz", ".rar")
    thread_pool = ThreadPool()
    futures = []

    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        name, ext = os.path.splitext(filename)

        if ext.lower() not in supported_ext or not os.path.isfile(file_path):
            continue

        target_dir = os.path.join(output_folder, name)
        os.makedirs(target_dir, exist_ok=True)

        future = thread_pool.submit(_unpack_single, file_path, target_dir, log_func)
        futures.append(future)

    # ✅ 等待所有任务完成后再返回
    for f in futures:
        f.result()

    log_func("🎉 所有压缩文件已解压完成")


def _unpack_single(file_path, target_dir, log_func):
    try:
        if zipfile.is_zipfile(file_path):
            with zipfile.ZipFile(file_path, 'r') as zf:
                zf.extractall(target_dir)

        elif tarfile.is_tarfile(file_path):
            with tarfile.open(file_path, 'r:*') as tf:
                tf.extractall(target_dir)

        elif file_path.endswith(".rar"):
            with rarfile.RarFile(file_path) as rf:
                rf.extractall(target_dir)

        else:
            raise ValueError(f"不支持的压缩格式：{file_path}")

        log_func(f"✅ 解压完成: {os.path.basename(file_path)}")
    except Exception as e:
        log_func(f"❌ 解压失败: {os.path.basename(file_path)} -> {e}")
