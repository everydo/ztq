#coding:utf-8
'''
功能描述: 此模块用于数据整合, 被views模块调用.

Created on 2011-4-28

@author: Zay
'''
import time, pprint, datetime
import ztq_core
import urllib
try:
    import json
except: import simplejson as json

def get_sys_log(sindex=None, eindex=None):
    log_queue = ztq_core.get_system_log_queue()
    for log in log_queue[sindex:eindex]:
        log['_alias'] = log.get('alias', '')
        log['_host'] = log.get('host', '')
        log['_type'] = log.get('type', '')
        log['_timestamp'] = datetime.datetime.fromtimestamp(log.get('timestamp', 0))
        yield log

def get_worker_log(sindex=None, eindex=None):
    worker_log_queue = ztq_core.get_work_log_queue()
    for worker_log in worker_log_queue[sindex:eindex]:
        # 检查worker是否还存在
        log = {}
        log['_server'] = worker_log['runtime']['worker']
        log['_created'] = datetime.datetime.fromtimestamp(worker_log['runtime'].get('create', 0))
        log['_start'] = datetime.datetime.fromtimestamp(worker_log['runtime'].get('start', 0))
        log['_end'] = datetime.datetime.fromtimestamp(worker_log['runtime'].get('end', 0))
        log['_status'] = worker_log['runtime']['return']
        log['_func'] = worker_log['func']
        log['_comment'] = worker_log['process'].get('comment','')
        log['_file'] = worker_log['kw'].get('comment', worker_log['kw'].get('path', ''))
        log['_reason'] = ''.join(worker_log['runtime']['reason'])
        log['_detail'] = pprint.pformat(worker_log)
        yield log
        
def get_taskqueues_list():
    # 队列情况列表
    dispatcher_config = ztq_core.get_dispatcher_config()
    queue_weight = dispatcher_config['queue_weight']
    queues_list = ztq_core.get_queue_config()

    # 排序
    sort_queue_name = {}
    for queue_name, queue_config in queues_list.items():
        sort_queue_name[queue_name] = len(ztq_core.get_error_queue(queue_name))
    
    for queue_name in sorted(sort_queue_name, 
                            key=lambda x: sort_queue_name[x], 
                            reverse=True):
        task_queue = {}
        task_queue['name'] = queue_name
        #task_queue['tags'] = queue_config.get('tags',())
        queue = ztq_core.get_task_queue(queue_name)
        # 任务数/错误数
        task_queue['length'] = len(queue)
        task_queue['error_length'] = sort_queue_name[queue_name]

        #任务首个时间
        task_queue['error_end'] = task_queue['first'] = ''
        first_job = queue[0]
        first_job= ztq_core.get_task_hash(queue_name).get(first_job)
        if first_job:
            task_queue['first'] = datetime.datetime.fromtimestamp(first_job['runtime'].get('create', 0))
        
        #错误最末一个的时间
        error_first_job = ztq_core.get_error_queue(queue_name)[0]
        error_first_job = ztq_core.get_error_hash(queue_name).get(error_first_job)
        if error_first_job:
            task_queue['error_end'] = datetime.datetime.fromtimestamp(error_first_job['runtime'].get('create', 0))

        task_queue['weight'] = queue_weight.get(queue_name, 0)
        # 获取worker工作线程配置
        workers_config = ztq_core.get_worker_config()
        task_queue['from_right'] = True
        for worker_name,worker_config in workers_config.items():
            task_queue['workers'] = []
            for config in worker_config.get(queue_name,[]):
                task_queue['workers'].append([worker_name+':', config['interval']])
                if 'from_right' in config:
                    task_queue['from_right'] = config['from_right']
        task_queue['buffer_length'] = len(ztq_core.get_buffer_queue(queue_name))
        yield task_queue

def get_queues_jobs(queue_name):
    queue = ztq_core.get_task_queue(queue_name)
    for task_job_hash in queue.reverse():
        task_job = ztq_core.get_task_hash(queue_name).get(task_job_hash)
        tmp_job={}
        tmp_job['_queue_name'] = queue_name
        tmp_job['_id'] = urllib.quote(task_job_hash)
        #tmp_job['_ori'] = task_job
        tmp_job['_detail'] = pprint.pformat(task_job)
        tmp_job['_created'] = datetime.datetime.fromtimestamp(task_job['runtime'].get('create', 0))
        yield tmp_job

def get_all_error_jobs(sindex=0, eindex=-1):
    queues_list = ztq_core.get_queue_config()
    index = 0
    count = eindex - sindex
    for queue_name in queues_list.keys():
        error_len = len(ztq_core.get_error_queue(queue_name))
        if error_len == 0: continue
        # 确定从哪里开始
        index += error_len
        if index < sindex: continue
        
        start_index = 0 if sindex-(index-error_len) < 0 else sindex-(index-error_len)
        yield get_error_queue_jobs(queue_name, start_index, count+start_index)

        # 是否应该结束
        count -= error_len - start_index
        if count < 0: break

def get_error_queue(error_queue_name, sindex=0, eindex=-1):
    """ 模板问题的原因 """
    yield get_error_queue_jobs(error_queue_name, sindex, eindex)

def get_error_queue_jobs(error_queue_name, sindex=0, eindex=-1):
    error_queue = ztq_core.get_error_queue(error_queue_name)
    workers_state = ztq_core.get_worker_state()
    for hash_key in error_queue[sindex:eindex]:
        error_job = ztq_core.get_error_hash(error_queue_name)[hash_key]
        tmp_job={}
        tmp_job['json'] = json.dumps(error_job)
        tmp_job['_queue_name'] = error_queue_name
        worker_name = error_job['runtime']['worker']
        # 检查worker是否存在,存在则取得服务器ip
        if worker_name in workers_state:
            tmp_job['_server'] = workers_state[worker_name]['ip']
        else: tmp_job['_server'] = worker_name
        tmp_job['_created'] = datetime.datetime.fromtimestamp(error_job['runtime'].get('create',0))
        tmp_job['_start'] = datetime.datetime.fromtimestamp(error_job['runtime'].get('start',0))
        tmp_job['_end'] = datetime.datetime.fromtimestamp(error_job['runtime'].get('end',0))
        tmp_job['_reason'] = ''.join(error_job['runtime']['reason'])
        tmp_job['_file'] = error_job['kw'].get('comment', error_job['kw'].get('path', ''))
        tmp_job['_error_mime'] = error_job['process'].get('to_mime','')
        tmp_job['_detail'] = pprint.pformat(error_job)
        tmp_job['hash_id'] = urllib.quote(hash_key)
        yield tmp_job

def get_worker_list():
    dispatcher_config = ztq_core.get_dispatcher_config()
    worker_weight = dispatcher_config['worker_weight']
    workers_dict = ztq_core.get_worker_state().items()
    for worker_name, worker_status in workers_dict:
        worker_status['_worker_name'] = worker_name
        worker_status['_started'] = \
            datetime.datetime.fromtimestamp(worker_status['started'])
        worker_status['_timestamp'] = \
            datetime.datetime.fromtimestamp(worker_status['timestamp'])
        worker_status['_worker_weight'] = worker_weight.get(worker_name, 0)
        # 检查worker是否在工作
        cmd_queue = ztq_core.get_command_queue(worker_name)
        # 如果指令队列不为空的话,意味着worker没工作,属于下线状态
        if cmd_queue: worker_status['_active'] = u'shutdown'
        elif worker_status['_worker_weight'] == 0: 
            worker_status['_active'] = u'ldle'
        else: worker_status['_active'] = u'work'
        # 获取worker开了多少个线程
        worker_job = ztq_core.get_job_state(worker_name)
        worker_status['_threads'] = []
        for thread_name,thread_status in worker_job.items():
            thread_status['_detail'] = pprint.pformat(thread_status)
            thread_status['_name'] = thread_name
            thread_status['_comment'] = thread_status['kw'].get('comment',thread_status['process'].get('comment', ''))
            thread_status['_pid'] = thread_status['process'].get('pid', -1)
            ident = unicode(thread_status['process'].get('ident', -1))
            if ident in worker_status['traceback']:
                thread_status['_thread_detail'] = pprint.pformat(worker_status['traceback'][ident])
            # 任务进行了多少时间
            used_time = int(time.time())-thread_status['process']['start']
            if used_time > 3600:
                used_time = u'%.2f小时' % (used_time / 3600.0)
            elif used_time > 60:
                used_time = u'%.2f分钟' % (used_time / 60.0)
            thread_status['_take_time'] = used_time

            worker_status['_threads'].append(thread_status)

        yield worker_status
        
def send_command(worker_name, command_stm):
    """向worker发报告状态指令
    """
    send_command= {
    'command':command_stm,
    'timestamp':int(time.time())
    }
    cmd_queue = ztq_core.get_command_queue(worker_name)
    
    # 避免同时发送多条同步命令
    if cmd_queue:
        for command in cmd_queue:
            if command.get('command', None) == send_command['command']:            
                return 0
    cmd_queue.push(send_command)
