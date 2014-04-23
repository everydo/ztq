#coding:utf-8
"""
功能描述:调度算法模块, 根据服务器和队列的权重进行工作调度.
"""

import time
import ztq_core 

def update_queue_threads(worker_name, queue_name, action):
    """调整特定队列线程数量，可以增加或者减少
    """
    worker_config = ztq_core.get_worker_config()
    queue_config = worker_config[queue_name]
    if queue_config.get(queue_name, None):
        _config = queue_config[queue_name]

        # 生成新的配置信息
        if action == 'queue_down' : 
            _config.pop()
        elif action == 'queue_up' : 
            _config.append(_config[0])
        queue_config[queue_name] = _config

        worker_config[worker_name]= queue_config
        send_sync_command(worker_name)

def send_sync_command(worker_name):
    """向转换器下达同步指令
    """
    sync_command= {'command':'updateworker','timestamp':int(time.time())}
    cmd_queue = ztq_core.get_command_queue(worker_name)
    # 避免同时发送多条同步命令
    if cmd_queue:
        for command in cmd_queue:
            if command.get('command', None) == sync_command['command']:            
                return 0
    cmd_queue.push(sync_command)
                
                
