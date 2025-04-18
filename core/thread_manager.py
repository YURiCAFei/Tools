# 统一线程注册与清理模块
from PyQt5.QtCore import QThread

class ThreadManager:
    _instance = None

    def __init__(self):
        self.threads = []

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = ThreadManager()
        return cls._instance

    def register(self, thread: QThread):
        """注册一个线程以便退出时统一清理"""
        if thread not in self.threads:
            self.threads.append(thread)

    def cleanup(self):
        """强制退出所有已注册线程"""
        for thread in self.threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(2000)  # 最多等待 2 秒

        self.threads.clear()
