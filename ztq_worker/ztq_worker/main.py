# -*- encoding: utf-8 -*-

import sys, os
from command_thread import CommandThread
from config_manager import read_config_file
from command_execute import init_job_threads, set_job_threads
from system_info import get_ip

import ztq_core

def run():
    conf_file = ''
    # 用户指定一个配置文件
    if len(sys.argv) > 1:
        conf_file = sys.argv[1]

    config = read_config_file(conf_file)
    main(config)

def main(config):
    """ 主函数 

    config: {'server': {host:, port:, db:}
            }
    """

    server = config['server']
    # 动态注册task
    for module in server['modules'].split():
        try:
            __import__(module)
        except ImportError:
            modules = module.split('.')
            __import__(modules[0], globals(), locals(), modules[1])

    # 连结服务器
    redis_host = server['host']
    redis_port = int(server['port'])
    redis_db = int(server['db'])
    ztq_core.setup_redis('default', host=redis_host, port=redis_port, db=redis_db)

    # 开启一个命令线程
    alias = server.get('alias', '')
    if not alias:
        alias = get_ip()
        server['alias'] = alias

    command_thread = CommandThread(worker_name=alias)

    sys.stdout.write('Starting server in PID %s\n'%os.getpid())

    worker_state = ztq_core.get_worker_state()
    active_config = server.get('active_config', 'false')

    # 计算那些是需要根据线上配置启动的队列
    active_queue_config = {} 
    if active_config.lower() == 'true' and command_thread.worker_name in worker_state:
        # 如果服务器有这个机器的配置信息，需要自动启动工作线程
        worker_config = ztq_core.get_worker_config()
        active_queue_config = worker_config.get(command_thread.worker_name, {})

    # 根据本地配置，启动的队列
    local_queue_config = {}
    if config['queues']:
        # 把worker监视队列的情况上报到服务器
        queue_config = ztq_core.get_queue_config()
        # 如果配置有queues，自动启动线程监视
        for queue_name, sleeps in config['queues'].items():
            # 线上配置稍后再设置
            if queue_name in active_queue_config: continue

            local_queue_config[queue_name] = [
                    {'interval': int(sleep)} for sleep in sleeps.split(',')
                    ]
            if not queue_config.get(queue_name, []):
                queue_config[queue_name] = {'name':queue_name, 'title':queue_name, 'widget': 5}


    # 合并线上和线下的配置
    active_queue_config.update(local_queue_config)
    init_job_threads(active_queue_config)

    loggers = config['log']
    initlog(
        loggers.get('key', 'ztq_worker'), 
        loggers.get('handler_file'), 
        loggers.get('level', 'ERROR'),
        )

    # 不是以线程启动
    command_thread.run()

def initlog(key, handler_file, level):
    import logging
    level = logging.getLevelName(level)
    format = '%(asctime)s %(message)s'
    if not handler_file:
        logging.basicConfig(level=level, format=format)
    else:
        logging.basicConfig(
                filename=handler_file, 
                filemode='a', 
                level=level, 
                format=format
                )
