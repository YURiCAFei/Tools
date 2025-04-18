from concurrent.futures import ThreadPoolExecutor


class ThreadPool:
    _instance = None

    def __new__(cls, max_workers=5):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.executor = ThreadPoolExecutor(max_workers=max_workers)
        return cls._instance

    def submit(self, func, *args, **kwargs):
        return self.executor.submit(func, *args, **kwargs)

    def shutdown(self, wait=True):
        self.executor.shutdown(wait=wait)
        ThreadPool._instance = None
