#coding:utf-8
"""
功能描述:调度算法模块, 根据服务器和队列的权重进行工作调度.
"""

import time
import ztq_core 

def dispatch_single_queue(queue_name, from_right=True):
    """调整特定队列, 让worker从队列头或者从队列尾获取数据
    """
    worker_config = ztq_core.get_worker_config()
    for worker_name, queue_config in worker_config.items():
        if queue_config.get(queue_name, None):
            queue_config[queue_name] = update_queue_config(queue_config[queue_name], from_right)
            worker_config[worker_name]= queue_config
            send_sync_command(worker_name)
            
def update_queue_config(queue_config, from_right):
    """生成新的配置信息
    """
    for config in queue_config:
        config['from_right'] = from_right
    return queue_config

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
                
                
