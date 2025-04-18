import os
import datetime
import atexit

class LogManager:
    def __init__(self, project_path):
        self.project_path = project_path
        self.buffer = []  # 日志缓存（待写入）
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        self.log_file = os.path.join(self.project_path, f"log_{timestamp}.txt")

        # 退出时自动写入
        atexit.register(self.flush)

    def log(self, text, to_console=True):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
        line = f"[{timestamp}] {text}"
        self.buffer.append(line)
        if to_console:
            print(line)  # 控制台输出（可改为 UI 调用）

    def flush(self):
        if not self.buffer:
            return
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write("\n".join(self.buffer) + "\n\n")
            self.buffer.clear()
        except Exception as e:
            print(f"⚠️ 写入日志失败: {e}")
