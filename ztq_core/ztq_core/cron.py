#coding:utf-8

""" 有一个定时执行的list: ztq:list:cron

放进去的工作，会定期自动执行
"""
from threading import Thread
import datetime
import time
import model
from task import split_full_func_name, push_task


def has_cron(func):
    if type(func) == str:
        func_name = func
    else:
        func_name = func.__raw__.__name__
    for cron in model.get_cron_set():
        if cron['func_name'] == func_name:
            return True
    return False

def add_cron(cron_info, full_func, *args, **kw):
    """ 定时执行 

    cron_info： {'minute':3, 'hour':3,}
    """
    cron_set = model.get_cron_set()
    if type(full_func) == str:
        queue_name, func_name = split_full_func_name(full_func)
    else:
        queue_name = full_func._ztq_queue
        func_name = full_func.__raw__.__name__
    cron_set.add({'func_name':func_name, 
                'cron_info':cron_info,
                'queue': queue_name,
                'args':args,
                'kw':kw})

def remove_cron(func):
    cron_set = model.get_cron_set()
    if type(func) == str:
        func_name = func
    else:
        func_name = func.__raw__.__name__
    for cron in cron_set:
        if cron['func_name'] == func_name:
            cron_set.remove(cron)

class CronThread(Thread):
    """ 定时检查cron列表，如果满足时间条件，放入相关的队列 """
    def __init__(self):
        super(CronThread, self).__init__()

    def run(self):
        """
            获取cron_info信息格式:{'minute':3, 'hour':3,}
        """
        cron_set = model.get_cron_set()
        while True:
            # 遍历cron列表检查并检查定时执行信息
            for cron in cron_set:
                execute_flag = self.check_cron_info(cron['cron_info'])
                if execute_flag:
                    push_task(cron['queue'] + ':' + cron['func_name'], *cron['args'], **cron['kw'])

            time.sleep(55)

    def check_cron_info(self, cron_info):
        """检查定时执行信息是否满足条件
        """
        time_now = datetime.datetime.now()
        hour_cron = int(cron_info.get('hour', -1)) 
        if hour_cron != -1:
            hour_now = int(time_now.hour)
            if hour_now != hour_cron:
                return False

        minute_cron = int(cron_info.get('minute', 0))
        minute_now = int(time_now.minute)
        if minute_cron != minute_now:
            return False
        return True


