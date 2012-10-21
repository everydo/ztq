# -*- coding: utf-8 -*-

from job_thread import JobThread
import time
from threading import Thread
import sys

# 需要退出的工作线程列表
kill_threads = []

class JobThreadManager:
    """ 管理工作线程， 开启/停止工作线程 """
    # 保存工作线程的信息
    # threads = {'thread-1':<object JobThread>, 'thread-2':<object JobThread>}
    threads = {}

    def add(self, queue_name, sleep_time, from_right=True):
        """ 开启一个工作线程 """
        job_thread = JobThread(queue_name, sleep_time, from_right)
        job_thread.setDaemon(True)
        job_thread.start()
        self.threads[job_thread.getName()] = job_thread
        sys.stdout.write(
                'start a job thread, name: %s,'
                ' ident: %s,'
                ' queue_name: %s\n'
                % (job_thread.getName(), job_thread.ident, queue_name)
                )

    def stop(self, job_name):
        """ 安全的停止一个工作线程
            正在转换中的时候，会等待转换完成后自动退出
        """
        if not job_name in self.threads:
            return
        #sys.stdout.write('stop %s job thread\n'% job_name)
        job_thread = self.threads[job_name]
        job_thread.stop()
        del self.threads[job_name]
        #kill_threads.append( dict( job_thread=job_thread,
        #                                timestamp = int(time.time()),
        #                                timeout = 5, )
        #                        )

class KillThread(Thread):
    """ 监视工作线程的退出 
        如果一定时间没有自动退出，就杀死
    """

    sleep_time = 300

    def run(self):
        while True:
            time.sleep(self.sleep_time)
            wake_time = int(time.time())

            for job in kill_threads:
                job_thread, timestamp, timeout = job.values()
                if not job_thread.is_alive(): # 已经死掉了
                    kill_threads.remove(job)
                    continue
                if wake_time - timestamp < 1: # 任务卡死了
                    #job._exit()
                    kill_threads.remove(job)
