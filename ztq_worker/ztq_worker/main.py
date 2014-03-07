# -*- encoding: utf-8 -*-

import sys, os
from command_thread import CommandThread
from config_manager import init_config
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
    alias = server['alias']
    if not alias:
        alias = get_ip()
    command_thread = CommandThread(worker_name=alias)

    sys.stdout.write('Starting server in PID %s\n'%os.getpid())

    worker_state = ztq_core.get_worker_state()
    active_config = server.get('active_config', 'false')
    if active_config.lower() == 'true' and command_thread.worker_name in worker_state:
        # 如果服务器有这个机器的配置信息，需要自动启动工作线程
        queue = ztq_core.get_worker_config()
        if command_thread.worker_name in queue:
            set_job_threads(queue[command_thread.worker_name])
    elif config['queues']:
        # 把worker监视队列的情况上报到服务器
        queue_config = ztq_core.get_queue_config()
        # 如果配置有queues，自动启动线程监视
        job_threads = {}
        for queue_name, sleeps in config['queues'].items():
            job_threads[queue_name] = [
                    {'interval': int(sleep)} for sleep in sleeps.split(',')
                    ]
            if not queue_config.get(queue_name, []):
                queue_config[queue_name] = {'name':queue_name, 'title':queue_name, 'widget': 5}

        init_job_threads(job_threads)

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
