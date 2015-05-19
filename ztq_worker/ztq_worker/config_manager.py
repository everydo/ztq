# -*- encoding: utf-8 -*-

import os 

from ConfigParser import SafeConfigParser as ConfigParser
from system_info import get_ip

# 读取配置文件（app.ini），保存到CONFIG中，实际使用的都是CONFIG
CONFIG = {'server':{'alias':get_ip()},
          'queues':{} }

def read_config_file(location=None):
    """ 初始化配置管理
    """
    cfg = ConfigParser()
    if location:
        cfg.read(location)
    else:
        local_dir = os.path.dirname(os.path.realpath(__file__))
        cfg.read( os.path.join(local_dir, 'config.cfg') )

    global CONFIG
    for section in cfg.sections():
        CONFIG[section] = {}
        for option in cfg.options(section):
            CONFIG[section][option] = cfg.get(section, option)
    return CONFIG


def register_batch_queue(queue_name, batch_size, batch_func=None):
    """ 注册队列是批处理模式
        queue_name: 指定哪个队列为批处理模式
        batch_size: 整形
        batch_func: 方法对象

        可以让队列在完成batch_size 后，执行一次 batch_func
    """
    CONFIG.setdefault('batch_queue', {}).update(
                {queue_name:{'batch_size':batch_size, 'batch_func':batch_func}})

