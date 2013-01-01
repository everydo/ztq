# -*- coding: utf-8 -*-

from job_thread import JobThread
import sys

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
