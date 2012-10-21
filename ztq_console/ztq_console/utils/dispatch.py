#coding:utf-8
"""
功能描述:调度算法模块, 根据服务器和队列的权重进行工作调度.
"""

import time
import ztq_core 


def dispatch():
    """根据调度参数进行转换器和队列的调度
    """
    #获取调度参数
    dispatcher_config = ztq_core.get_dispatcher_config()
    worker_weight = dispatcher_config['worker_weight']
    if not worker_weight: return
    queue_weight = dispatcher_config['queue_weight']
    worker_list = ztq_core.get_all_worker()
    
    #生成新的转换器工作线程配置
    if worker_list:
        gen_worker_config(worker_weight, queue_weight, worker_list) 

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
        
def gen_worker_config(worker_weight, queue_weight, worker_list):
    """生成新的转换器工作线程配置
       输出参数:{'q01':[{ 'interval':5}],  # 间隔时间
             'q02':[{'interval':5},{'interval':3}],
            }
    """
    #获取转换器的工作线程配置
    worker_config = ztq_core.get_worker_config()
    for worker in worker_list:        
        new_config = {}

        # 如果worker的权重为0则配置为空
        if worker_weight.get(worker, '') == 0: 
            worker_config[worker]= new_config
            send_sync_command(worker)
            continue
        
        #根据原子队列权重和转换器权重更新工作线程配置
        for queue,queue_weight in queue_weight.iteritems(): 
            new_config[queue] = []         
            #根据原子队列权重进程更新工作线程配置
            if queue_weight < 1 :
                new_config[queue].append(gen_new_config(9))
            elif queue_weight < 2 :
                new_config[queue].append(gen_new_config(7))
            elif queue_weight < 3 :
                new_config[queue].append(gen_new_config(6))
            elif queue_weight >= 3 and queue_weight < 5 :
                new_config[queue].append(gen_new_config(4))
            elif queue_weight == 5:
                new_config[queue].append(gen_new_config(0))
            elif queue_weight >= 5 and worker_weight[worker] <= 6:
                new_config[queue].append(gen_new_config(0))
                new_config[queue].append(gen_new_config(0))
            elif queue_weight >= 6 and worker_weight[worker] <= 7:
                new_config[queue].append(gen_new_config(1))
                new_config[queue].append(gen_new_config(1))
                new_config[queue].append(gen_new_config(1))
            elif queue_weight >= 7 and worker_weight[worker] > 7:
                new_config[queue].append(gen_new_config(0))
                new_config[queue].append(gen_new_config(0)) 
                new_config[queue].append(gen_new_config(1))
            
        worker_config[worker]= new_config
        send_sync_command(worker)

def gen_new_config(interval):
    """生成新的配置信息
    """
    return dict(interval=interval)

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
                
                
