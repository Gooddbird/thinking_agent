import time


class TimeUtil:
    @staticmethod
    def get_now_time_14_str():
        return time.strftime('%Y%m%d%H%M%S', time.localtime())