#coding:utf-8
""" redis任务队列
"""

import model
import time
from threading import Thread
from hashlib import md5
from redis_wrap import dump_method

task_registry = {}

def register(func, func_name = None):
    """ 注册task

    定义::

      def echo(aaa, bb, c=1):
          print aaa, bb, c

    注册远端任务::

      from zopen_redis import task_registry
      task_registry.register(echo)
    """
    task_registry[func_name or func.__name__] = func

def split_full_func_name(full_func_name):
    splitted_func_name = full_func_name.rsplit(':', 1)
    # 如果没有，就到默认队列
    if len(splitted_func_name) == 1:
        return 'default', full_func_name
    else:
        return splitted_func_name

def gen_task(func_name, *args, **kw):
    callback = kw.pop('ztq_callback', '')
    callback_args = kw.pop('ztq_callback_args', ()) 
    callback_kw = kw.pop('ztq_callback_kw', {})

    fcallback = kw.pop('ztq_fcallback', '')
    fcallback_args = kw.pop('ztq_fcallback_args', ()) 
    fcallback_kw = kw.pop('ztq_fcallback_kw', {})

    pcallback = kw.pop('ztq_pcallback', '')
    pcallback_args = kw.pop('ztq_pcallback_args', ()) 
    pcallback_kw = kw.pop('ztq_pcallback_kw', {})
    return {'func':func_name,
                'args':args,
                'kw':kw, 

                'callback':callback,
                'callback_args':callback_args,
                'callback_kw':callback_kw,

                'fcallback':fcallback,
                'fcallback_args':fcallback_args,
                'fcallback_kw':fcallback_kw,

                'pcallback':pcallback,
                'pcallback_args':pcallback_args,
                'pcallback_kw':pcallback_kw,
            }

def _get_task_md5(task):
    """ 得到task(dict) 的md5值 """
    #_value = json.dumps(task, sort_keys=True)
    _value = dump_method['json'](task)

    return md5(_value).digest()

def push_buffer_task(full_func_name, *args, **kw):
    queue_name, func_name = split_full_func_name(full_func_name)
    task = gen_task(func_name, *args, **kw)
    model.get_buffer_queue(queue_name).push(task)

def push_task(full_func_name, *args, **kw):
    """
    callback: 这是另外一个注册的task，在func调用完毕后，会启动这个

    加入队列::

     task_regitry.push(u'foo:echo', aaa, bb, foo='bar', 
            callback='foo:callback', callback_args=(12,32,3), callback_kw={}) 
    """
    system = kw.get('ztq_system', 'default')
    queue_name, func_name = split_full_func_name(full_func_name)
    to_right = kw.pop('ztq_first', False)
    # 队列运行相关信息
    runtime = kw.pop('runtime', \
            {'create':int(time.time()), 'queue':queue_name})

    task = gen_task(func_name, *args, **kw)
    task_md5 = _get_task_md5(task)

    task_hash = model.get_task_hash(queue_name, system=system)

    # 因为queue队列有worker不停在监视,必须先将hash的内容push,在将queue的内容push
    task['runtime'] = runtime
    if task_hash.__setitem__(task_md5, task) == 1:
        # 如果返回值等于0， 说明task_md5已经存在
        queue = model.get_task_queue(queue_name, system=system)
        queue.push(task_md5, to_left=not to_right)

def push_runtime_task(queue_name, task):
    """ 直接将task push 到 redis """
    _push_runtime_job(queue_name, task, model.get_task_hash, model.get_task_queue)

def push_runtime_error(queue_name, error):
    _push_runtime_job(queue_name, error, model.get_error_hash, model.get_error_queue)

def _push_runtime_job(queue_name, task, get_hash, get_queue):
    to_left = task.get('kw', {}).pop('to_left', True)
    runtime = task.pop('runtime') 

    task_md5 = _get_task_md5(task)
    task_hash = get_hash(queue_name)

    # 因为queue队列有worker不停在监视,必须先将hash的内容push,在将queue的内容push
    task['runtime'] = runtime
    if task_hash.__setitem__(task_md5, task) == 1:
        # 如果返回值等于0， 说明task_md5已经存在
        queue = get_queue(queue_name)
        queue.push(task_md5, to_left=to_left)

def pop_task(queue_name, task_md5=None, timeout=0, from_right=True):
    """ 取出，并删除 """
    return _pop_job(queue_name, task_md5, 
            model.get_task_hash, model.get_task_queue, timeout, from_right)

def pop_error(queue_name, task_md5=None, timeout=0, from_right=True):
    return _pop_job(queue_name, task_md5, 
            model.get_error_hash, model.get_error_queue, timeout, from_right)

def _pop_job(queue_name, task_md5, get_hash, get_queue, timeout=0, from_right=True):

    if not task_md5:
        task_md5 = get_queue(queue_name).pop(timeout=timeout, \
                from_right=from_right)
    else:
        get_queue(queue_name).remove(task_md5)

    if not task_md5: return None # 可能超时了

    task_hash = get_hash(queue_name)
    return task_hash.pop(task_md5)

class JobThread(Thread):
    def __init__(self,queue_name):
        super(JobThread,self).__init__()
        self.queue_name = queue_name

    def run(self):
        """ 阻塞方式找到任务，并自动调用"""
        queue = model.get_task_queue(self.queue_name)
        while True:
            task = queue.pop()
            try:
                task_registry[task['func']](*task['args'], **task['kw'])
                if task['callback']:
                    callback_args = task.get('callback_args', ())
                    callback_kw = task.get('callback_kw', {})
                    push_task(task['callback'], *callback_args, **callback_kw)
            except Exception, e:
                print str(e)

def has_task(queue_name, task, to_front=False):
    """ 检查是否存在某个job
    在queue_name的队列上，在arg_index的位置，对于func_name, 值为arg_value 
    如果不存在，返回false， 在worker中工作，返回‘work'， 队列中返回’queue'
    """
    runtime = task.pop('runtime', None)
    task_md5 = _get_task_md5(task)
    if not runtime is None: task['runtime'] = runtime

    # 检查work现在的工作
    worker_list = model.get_all_worker()
    for worker_name in worker_list:
        worker_job = model.get_job_state(worker_name)
        if not worker_job: continue
        for thread_name, job in worker_job.items():
            job.pop('runtime', '')
            job.pop('process', '')
            if _get_task_md5(job) == task_md5:
                return 'running'

    # 检查所在队列
    queue_name = queue_name 
    task_hash = model.get_task_hash(queue_name)
    if task_md5 in task_hash:
        if to_front: # 调整顺序
            task_queue = model.get_task_queue(queue_name)
            task_queue.remove(task_md5)
            task_queue.push(task_md5, to_left=False)
        return 'queue'

    return 'none'

