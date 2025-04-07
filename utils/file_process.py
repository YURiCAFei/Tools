# utils/decompress.py

import os
import zipfile
import tarfile
import subprocess
import shutil

try:
    import rarfile
    HAS_RARFILE = True
except ImportError:
    HAS_RARFILE = False


def is_archive_file(filename: str) -> bool:
    f = filename.lower()
    return (
        f.endswith(".zip") or
        f.endswith(".tar") or
        f.endswith(".tar.gz") or
        f.endswith(".tgz") or
        f.endswith(".tar.bz2") or
        f.endswith(".tbz") or
        f.endswith(".tbz2") or
        f.endswith(".tar.xz") or
        f.endswith(".txz") or
        (HAS_RARFILE and f.endswith(".rar"))
    )


def extract_archive(input_path, output_dir=".", log_callback=None, progress_callback=None, stop_check=None):
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    def should_stop():
        return stop_check and stop_check()

    input_path_lower = input_path.lower()

    if input_path_lower.endswith(".zip"):
        with zipfile.ZipFile(input_path, "r") as zf:
            members = zf.infolist()
            total = len(members)
            for i, member in enumerate(members, 1):
                if should_stop(): return
                zf.extract(member, path=output_dir)
                if progress_callback:
                    progress_callback(i / total)
        log(f"✔ 解压 zip 成功: {input_path}")

    elif input_path_lower.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz", ".tbz2", ".tar.xz", ".txz")):
        with tarfile.open(input_path, "r:*") as tf:
            members = tf.getmembers()
            total = len(members)
            for i, member in enumerate(members, 1):
                if should_stop(): return
                tf.extract(member, path=output_dir)
                if progress_callback:
                    progress_callback(i / total)
        log(f"✔ 解压 tar 成功: {input_path}")

    elif input_path_lower.endswith(".rar") and HAS_RARFILE:
        with rarfile.RarFile(input_path) as rf:
            members = rf.infolist()
            total = len(members)
            for i, member in enumerate(members, 1):
                if should_stop(): return
                rf.extract(member, path=output_dir)
                if progress_callback:
                    progress_callback(i / total)
        log(f"✔ 解压 rar 成功: {input_path}")

    else:
        log(f"❌ 不支持的压缩格式: {input_path}")


def decompress_process(path, output_dir=None, log_callback=None, progress_callback=None, stop_check=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    if not output_dir:
        log("❌ 必须指定输出目录")
        return

    if os.path.isfile(path):
        if is_archive_file(path):
            extract_archive(path, output_dir, log_callback, progress_callback, stop_check)
        else:
            log("⚠️ 非压缩文件，跳过")

    elif os.path.isdir(path):
        archives = [f for f in os.listdir(path) if is_archive_file(f)]
        total = len(archives)
        for idx, fname in enumerate(archives, 1):
            full_path = os.path.join(path, fname)
            out_dir = os.path.join(output_dir, os.path.splitext(fname)[0])
            os.makedirs(out_dir, exist_ok=True)

            extract_archive(
                full_path,
                out_dir,
                log_callback,
                lambda p: progress_callback(((idx - 1) + p) / total) if progress_callback else None,
                stop_check
            )
    else:
        log("❌ 输入路径无效")
