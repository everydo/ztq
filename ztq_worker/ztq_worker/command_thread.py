# -*- encoding: utf-8 -*-

from config_manager import CONFIG
from command_execute import report, kill_transform, cancel_transform, set_job_threads
from threading import Thread
import time
import ztq_core

class CommandThread(Thread):
    """ 监视命令队列，取得命令, 执行命令"""

    def __init__(self, worker_name=''):
        super(CommandThread, self).__init__()
        self.login_time = int(time.time())
        self.worker_name = worker_name or CONFIG['server']['alias']

    def init(self):
        """ 开机初始化工作 """
        reboot = False
        worker_state = ztq_core.get_worker_state()
        if self.worker_name in worker_state:
            # 重启，读取服务器配置信息
            reboot = True
        # 记录系统日志
        system_log = ztq_core.get_system_log_queue()
        system_log.push(dict( host=CONFIG['server']['alias'],
                              alias=self.worker_name,
                              type=reboot and 'reboot' or 'power',
                              timestamp=self.login_time,))
        # 报告机器状态
        worker_state[self.worker_name] = report(self.login_time)

    def run(self):
        self.init()
        # 监听指令
        commands = ztq_core.get_command_queue(self.worker_name)
        while True:
            try:
                command = commands.pop()
                if command['command'] == 'report':
                    worker_state = ztq_core.get_worker_state()
                    worker_state[self.worker_name] = report(self.login_time)
                elif command['command'] == 'updatedriver':
                    # TODO
                    #async_drive_config()
                    pass
                elif command['command'] == 'updateworker':
                    queue = ztq_core.get_worker_config()
                    set_job_threads(queue[self.worker_name])
                elif command['command'] == 'kill':
                    kill_transform(pid=command['pid'], timestamp=command['timestamp'])
                elif command['command'] == 'cancel':
                    cancel_transform(pid=command['pid'], timestamp=command['timestamp'])
            except KeyboardInterrupt:
                import os
                # 实际上调用的是command_execute.clear_thread
                os.sys.exitfunc()
                os._exit(0)
