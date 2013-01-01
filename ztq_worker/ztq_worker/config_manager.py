# -*- encoding: utf-8 -*-

import os 

from ConfigParser import ConfigParser
from system_info import get_ip

# 读取配置文件（app.ini），保存到CONFIG中，实际使用的都是CONFIG
CONFIG = {}

def init_config(location=None):
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

def set_config(config, section=''):
    """ 设置配置信息，默认设置全部，可选只设置某个节点 """
    global CONFIG
    if section:
        config = {section:config}

    for key, value in config.items():
        section = CONFIG.setdefault(key, {})
        section.update(value)

def get_configs(section):
    """ 得到节点全部的相关信息 """
    if CONFIG is None:
        return ''
    return CONFIG.get(section, {})

def get_config(section, option):
    """ 得到某个节点的某个值 """
    if CONFIG is None:
        return ''
    return CONFIG.get(section, {}).get(option, '')

def safe_get_host(section, option):
    """ 得到worker的的host name
        先找配置文件，是否配置了server节点下的alias 
        没有就返回worker机器的IP

        get_ip 方法已经缓存了结果
    """
    host = get_config(section, option)
    if not host:
        return get_ip()
    return host

def register_batch_queue(queue_name, batch_size, batch_func=None):
    """ 注册队列是批处理模式
        queue_name: 指定哪个队列为批处理模式
        batch_size: 整形
        batch_func: 方法对象

        可以让队列在完成batch_size 后，执行一次 batch_func
    """
    set_config(
            config={queue_name:{'batch_size':batch_size, 'batch_func':batch_func}}, 
            section="batch_queue",
            )
