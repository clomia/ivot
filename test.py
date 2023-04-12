from dotenv import load_dotenv

load_dotenv()
from system.logger import log
import multiprocessing

multiprocessing.set_start_method("fork")


def func(say_list):
    for say in say_list:
        log.info(say)


multiprocessing.Process(target=func, args=(["1", "1", "1", "1", "1", "1"],)).start()
multiprocessing.Process(target=func, args=(["2", "2", "2", "2", "2", "2"],)).start()
multiprocessing.Process(target=func, args=(["3", "3", "3", "3", "3", "3"],)).start()
multiprocessing.Process(target=func, args=(["4", "4", "4", "4", "4", "4"],)).start()
multiprocessing.Process(target=func, args=(["5", "5", "5", "5", "5", "5"],)).start()
log.info("안녕")
log.warning("만나서 반가워")
import time

time.sleep(3)
log.error("끝")
