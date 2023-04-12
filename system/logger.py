import platform
import psutil
import traceback
import logging
import logging.config
from functools import wraps
from contextlib import contextmanager
from datetime import datetime


class LogHandler(logging.NullHandler):
    def __init__(self):
        super().__init__()
        self.filename = "debug.log"
        self.today = datetime.now()
        with open(self.filename, "w") as file:
            file.write(
                f"Platform: {platform.platform()}\n"
                f"======= 시작: {self.today.year}년 {self.today.month}월 {self.today.day}일 =======\n\n"
            )

    def handle(self, record):
        print(f"[{record.processName}][{record.levelname}] {self.format(record)}")

        memory = psutil.virtual_memory()
        memory_used = memory.total - memory.available
        memory_percent = (memory_used / memory.total) * 100

        disk = psutil.disk_usage("/")
        disk_used = disk.total - disk.free
        disk_percent = (disk_used / disk.total) * 100

        memory_percent = f"{memory_percent:.0f}%"
        disk_percent = f"{disk_percent:.0f}%"
        memory_gb = f"{memory_used * 1e-9:.0f}GB"
        disk_gb = f"{disk_used * 1e-9:.0f}GB"

        system_status = (
            f"[메모리: {memory_gb}({memory_percent})][디스크: {disk_gb}({disk_percent})]"
        )

        now = datetime.now()
        time = f"[{now.hour}시 {now.minute}분 {now.second}초]"

        content = f"[{record.processName}][{record.levelname}][{record.module}({record.funcName})]{time}{system_status}\n{self.format(record)}"
        with open(self.filename, "a") as file:
            if self.today.day != now.day:
                self.today = now
                file.write(
                    f"\n======= {self.today.year}년 {self.today.month}월 {self.today.day}일 =======\n\n"
                )
            file.write(content + "\n")


log = logging.getLogger("logger")
log.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(message)s")
log_handler = LogHandler()
log_handler.setFormatter(formatter)
log_handler.setLevel("DEBUG")
log.addHandler(log_handler)


@contextmanager
def exception_handler(comment: str):
    """
    - 컨텍스트 안에서 발생하는 에러를 헨들링합니다.
    - (comment): 컨텍스트에 대한 한줄 설명
    """
    error_comment = comment + " 실행 중 에러 발생"
    try:
        log.debug(f"{comment} (start)")
        yield
        log.debug(f"{comment} (done)")
    except Exception as fatal_error:
        error_name = fatal_error.__class__.__name__
        log.critical(f"{error_comment}\n{error_name}\n{traceback.format_exc()}")
        raise fatal_error
    finally:
        pass


class ExceptionHandler:
    """callable 객체 안에서 발생하는 에러를 헨들링합니다."""

    def __init__(self, comment: str):
        self.comment = comment

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, comment="", **kwargs):
            comment = f"({comment})" if comment else ""
            log_content = f"[함수: {func.__qualname__}{comment}] {self.comment}"
            with exception_handler(comment=log_content):
                result = func(*args, **kwargs)
            return result

        return wrapper
