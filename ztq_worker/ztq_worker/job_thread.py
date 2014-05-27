# -*- encoding: utf-8 -*-
import threading
import time, sys
import traceback
import logging

from config_manager import CONFIG
import ztq_core

thread_context = threading.local()
logger = logging.getLogger("ztq_worker")
QUEUE_TIMEOUT = 30

def report_job(pid=-1, comment='', **kw):
    """ 报告当前转换进程信息 """
    if not hasattr(thread_context, 'job'):
        return  # 如果不在线程中，不用报告了

    job = thread_context.job

    # 报告转换状态
    job['process'].update({'pid': pid,
                        'start':int(time.time()),
                        'comment':comment})
    if kw:
        job['process'].update(kw)

    # 写入状态
    job_state = ztq_core.get_job_state(job['runtime']['worker'])
    job_state[job['runtime']['thread']] = job

def report_progress(**kw):
    """ 报告当前转换进程信息 """
    if not hasattr(thread_context, 'job'):
        return  # 如果不在线程中，不用报告了

    job = thread_context.job

    if not 'progress_callback' in job: return
    # 报告转换进度
    progress_func  = ztq_core.task_registry[job['pcallback']]
    progress_args = job.get('pcallback_args', [])
    progress_kw  = job.get('pcallback_kw', {})
    progress_kw.update(kw)
    progress_func(*progress_args, **progress_kw)

class JobThread(threading.Thread):
    """ 监视一个原子队列，调用转换引擎取转换
        转换结果记录转换队列，转换出错需要记录出错日志与错误队列
    """
    def __init__(self, queue_name, sleep_time, from_right=True):
        super(JobThread, self).__init__()
        self.queue_name = queue_name
        self.sleep_time = sleep_time
        self.from_right = from_right # 读取服务器队列的方向，从左边还是右边
        # _stop 为 True 就会停止这个线程
        self._stop = False
        self.start_job_time = 0  #  记录任务开始时间

    def run(self):
        """ 阻塞方式找到任务，并自动调用"""
        # 如果上次有任务在运行还没结束，重新执行
        jobs = ztq_core.get_job_state(CONFIG['server']['alias'])
        if self.name in jobs:
            self.start_job(jobs[self.name])

        # 队列批处理模式
        # batch_size: 批处理的阀值，达到这个阀值，就执行一次batch_func
        # batch_func: 
        #    1, 执行一批batch_size 大小的任务后，后续自动执行这个方法方法
        #    2, 执行一批小于batch_size 大小的任务后，再得不到任务，后续自动执行这个方法
        batch_config = CONFIG.get("batch_queue", {}).get(self.queue_name, {})
        batch_size = batch_config.get('batch_size', None) or -1
        batch_func = batch_config.get('batch_func', None) or (lambda *args, **kw: -1)

        run_job_index = 0
        queue_tiemout = QUEUE_TIMEOUT
        # 循环执行任务
        while not self._stop:
            try:
                task = ztq_core.pop_task(
                        self.queue_name, 
                        timeout=queue_tiemout, 
                        from_right=self.from_right
                        )
            except ztq_core.ConnectionError, e:
                logger.error('ERROR: redis connection error: %s' % str(e))
                time.sleep(3)
                continue
            except ztq_core.ResponseError, e:
                logger.error('ERROR: redis response error: %s' % str(e))
                time.sleep(3)
                continue
            except Exception, e:
                logger.error('ERROR: redis unknown error: %s' % str(e))
                time.sleep(3)
                continue

            if task is None: 
                # 没有后续任务了。执行batch_func
                if run_job_index > 0:
                    run_job_index = 0
                    queue_tiemout = QUEUE_TIMEOUT
                    try:
                        batch_func()
                    except Exception, e:
                        logger.error('ERROR: batch execution error: %s' % str(e))
                continue

            try:
                self.start_job(task)
            except Exception, e:
                logger.error('ERROR: job start error: %s' % str(e))

            if batch_size > 0: 
                if run_job_index >= batch_size - 1:
                    # 完成了一批任务。执行batch_func
                    run_job_index = 0
                    queue_tiemout = QUEUE_TIMEOUT
                    try:
                        batch_func()
                    except Exception, e:
                        logger.error('ERROR: batch execution error: %s' % str(e))
                else:
                    run_job_index += 1
                    queue_tiemout = -1

            if self.sleep_time:
                time.sleep(self.sleep_time)

    def start_job(self, task):
        self.start_job_time = int(time.time())
        task['runtime'].update({'worker': CONFIG['server']['alias'],
                                'thread': self.getName(),
                                'start': self.start_job_time, })
        # 记录当前在做什么
        task['process'] = {'ident':self.ident}
        thread_context.job = task
        try:
            # started report
            report_job(comment='start the job')
            self.run_task = ztq_core.task_registry[task['func']]
            self.run_task(*task['args'], **task['kw'])

            task['runtime']['return'] = 0
            task['runtime']['reason'] = 'success'

            if task.get('callback', None):
                callback_args = task.get('callback_args', ())
                callback_kw = task.get('callback_kw', {})
                ztq_core.push_task(task['callback'], *callback_args, **callback_kw)

        except Exception, e:
            reason = traceback.format_exception(*sys.exc_info())
            # 将错误信息记录到服务器
            try:
                return_code = str(e.args[0]) if len(e.args) > 1 else 300
            except:
                return_code = 300
            task['runtime']['return'] = return_code
            task['runtime']['reason'] = reason[-11:]
            task['runtime']['end'] = int( time.time() )
            ztq_core.push_runtime_error(self.queue_name, task)
            # 错误回调
            if task.get('fcallback', None):
                callback_args = task.get('fcallback_args', ())
                callback_kw = task.get('fcallback_kw', {})
                callback_kw['return_code'] = return_code
                callback_kw['return_msg'] = unicode(reason[-1], 'utf-8', 'ignore')
                ztq_core.push_task(task['fcallback'], *callback_args, **callback_kw)
            # 在终端打印错误信息
            #reason.insert(0, str(datetime.datetime.today()) + '\n')
            logger.error(''.join(reason))

        # 任务结束，记录日志
        task['runtime']['end'] = int( time.time() )
        ztq_core.get_work_log_queue().push(task)
        # 删除服务器的转换进程状态信息
        job_state = ztq_core.get_job_state(task['runtime']['worker'])
        del job_state[task['runtime']['thread']]
        self.start_job_time = 0

    def stop(self):
        """ 结束这个进程，会等待当前转换完成
            请通过JobThreadManager 来完成工作线程的退出，不要直接使用这个方法
        """
        self._stop = True

