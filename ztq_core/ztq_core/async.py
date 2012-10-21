# -*- encoding:utf-8 -*-

import types
from task import register, push_task, has_task, gen_task
import transaction

use_transaction = False

def _setup_callback(kw):
    callback = kw.pop('ztq_callback', None) 
    if callback is not None:
        callback_func, callback_args, callback_kw = callback
        callback_queue = callback_kw.pop('ztq_queue', callback_func._ztq_queue)
        kw.update({'ztq_callback':"%s:%s" % (callback_queue, callback_func.__raw__.__name__),
                   'ztq_callback_args':callback_args,
                   'ztq_callback_kw':callback_kw})
    fcallback = kw.pop('ztq_fcallback', None) 
    if fcallback is not None:
        callback_func, callback_args, callback_kw = fcallback
        callback_queue = callback_kw.pop('ztq_queue', callback_func._ztq_queue)
        kw.update({'ztq_fcallback':"%s:%s" % (callback_queue, callback_func.__raw__.__name__),
                   'ztq_fcallback_args':callback_args,
                   'ztq_fcallback_kw':callback_kw})
    pcallback = kw.pop('ztq_pcallback', None) 
    if pcallback is not None:
        callback_func, callback_args, callback_kw = pcallback
        callback_queue = callback_kw.pop('ztq_queue', callback_func._ztq_queue)
        kw.update({'ztq_pcallback':"%s:%s" % (callback_queue, callback_func.__raw__.__name__),
                   'ztq_pcallback_args':callback_args,
                   'ztq_fcallback_kw':callback_kw})

def async(*_args, **_kw):
    """ 这是一个decorator，事务提交的时候，提交到job队列，异步执行 

    定义job
    =============
    第一种::

        @async
        def say_hello(name):
            print 'hello, ', name

    第二种, 预先指定队列执行信息::

        @async(queue='hello_queue', transaction=True)
        def say_hello(name):
            print 'hello, ', name

    使用方法
    ================
    支持如下几种::

        say_hello('asdfa')
        say_hello('asdfa', ztq_queue="asdfa", ztq_transaction=False)

    """
    if len(_args) == 1 and not _kw and isinstance(_args[0], types.FunctionType): # 不带参数的形式
        func = _args[0]
        def new_func1(*args, **kw):
            queue_name = kw.pop('ztq_queue', 'default')
            on_commit= kw.pop('ztq_transaction', use_transaction) 
            task_name = "%s:%s" % (queue_name, func.__name__)
            _setup_callback(kw)
            if on_commit:
                add_after_commit_hook(push_task, (task_name,) + args, kw)
            else:
                push_task(task_name, *args, **kw)
        new_func1.__raw__ = func
        new_func1._ztq_queue = 'default'
        register(func)
        return new_func1
    else:
        _queue_name = _kw.get('queue', 'default')
        _on_commit= _kw.get('transaction', use_transaction) 
        def _async(func):
            def new_func(*args, **kw):
                on_commit= kw.pop('ztq_transaction', _on_commit) 
                queue_name = kw.pop('ztq_queue', _queue_name)
                task_name = "%s:%s" % (queue_name, func.__name__)
                _setup_callback(kw)
                if on_commit:
                    add_after_commit_hook(push_task, (task_name,) + args, kw)
                else:
                    push_task(task_name, *args, **kw)
            new_func.__raw__ = func
            new_func._ztq_queue = _queue_name
            register(func)
            return new_func
        return _async

def prepare_task(func, *args, **kw):
    _setup_callback(kw)
    return func, args, kw

def ping_task(func, *args, **kw):
    queue_name = kw.pop('ztq_queue', func._ztq_queue)
    to_front = kw.pop('ztq_first', False)
    on_commit = kw.pop('ztq_transaction', None)
    run = kw.pop('ztq_run', False)
    task = gen_task(func.__raw__.__name__, args, kw)
    result = has_task(queue_name, task, to_front=to_front)
    if result is None and run:
        kw['ztq_queue'] = queue_name
        kw['ztq_first'] = to_front
        if on_commit is not None:
            kw['ztq_transaction'] = on_commit
        func(*args, **kw)
    return result

#### 以下代码让队列的任务支持事务

def enable_transaction(enable):
    """ 是否支持transaction, 默认不支持 """
    global use_transaction
    use_transaction = bool(enable)

def _run_after_commit(success_commit, func, args, kw):
    if success_commit:
        func(*args, **kw)

def add_after_commit_hook(func, args, kw):
    """ 在事务最后添加一个钩子，让队列任务在事务完成后才做实际的操作
    """
    if not use_transaction: return 
    transaction.get().addAfterCommitHook(
                        _run_after_commit,
                        (func, args, kw),
                        )
