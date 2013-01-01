# -*- encoding: utf-8 -*-
import threading
import time

import ztq_core

class BufferThread(threading.Thread):

    def __init__(self, config):
        """ cofnig: {'job-0':{'thread_limit': 50},,,}
        """
        super(BufferThread, self).__init__()
        self.config = config
        self._stop = False

    def run(self):

        if not self.config: return 

        while not self._stop:
            for buffer_name, buffer_config in self.config.items():

                # 需要停止
                if self._stop: return

                self.buffer_queue = ztq_core.get_buffer_queue(buffer_name)
                self.task_queue = ztq_core.get_task_queue(buffer_name)
                self.buffer_name = buffer_name
                self.task_queue_limit = int(buffer_config['thread_limit'])

                while True:
                    try:
                        self.start_job()
                        break
                    except ztq_core.ConnectionError:
                        time.sleep(3)

            time.sleep(1)

    def start_job(self):
        over_task_limit = self.task_queue_limit - len(self.task_queue)

        # 这个任务可能还没有push上去，服务器就挂了，需要在重新push一次
        if getattr(self, 'buffer_task', None):
            self.push_buffer_task()

        # 相关的任务线程，处于繁忙状态
        if over_task_limit <= 0:
            return

        # 不繁忙，就填充满
        else:
            while over_task_limit > 1:

                # 需要停止
                if self._stop: return

                # 得到一个任务
                self.buffer_task = self.buffer_queue.pop(timeout=-1)
                if self.buffer_task is None:
                    return 

                self.push_buffer_task()

                self.buffer_task = None
                over_task_limit -= 1

    def push_buffer_task(self):
        if 'runtime' not in self.buffer_task:
            self.buffer_task['runtime'] = {}

        ztq_core.push_runtime_task(self.buffer_name, self.buffer_task)

    def stop(self):
        self._stop = True
