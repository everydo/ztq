
ZTQ：Zopen Task Queue
===========================================

简介
--------------------

ZTQ 队列服务, 分为3个包：ztq_core, ztq_worker, ztq_console。默认使用redis作为队列的后端。

ztq_core ::

    提供一系列的方法把任务push到队列中，由ztq_worker去获取队列任务并且执行。

你可以在这里找到它： http://pypi.python.org/pypi/ztq_core/

ztq_worker::

    队列的接收端，以线程为单位阻塞式的去监视一个队列。每一个线程称为Worker
    当有任务push到了队列中，相应的Worker会自动pull下来去执行。

你可以在这里找到它： http://pypi.python.org/pypi/ztq_worker/

ztq_console::

    对每一个队列的每一个任务执行情况进行监控、下达指令。这个包是可选的

你可以在这里找到它： http://pypi.python.org/pypi/ztq_console/

关于 ZTQ 
--------------------
:: 

    * 开源, 使用MIT 许可
    * 基于Python, 容易使用和修改
    * 支持linux 和 windows
    * 可靠，可以应付突然断电等情况
    * 可管理，自身带有ztq_console 监控后台
    * 灵活，可以在不同的机器上运行多个Worker, 并且随时热插拔Worker 
    * 使用简单

安装
--------------------
::

    pip install ztq_core
    pip install ztq_worker
    pip install ztq_console

使用
-------------------

#. 先定义一个普通的任务 ::

   #  my_send.py

    def send(body):
           print ‘START: ‘, body
           sleep(5)
           print ‘END:’, body


    def send2(body):
           print ‘START2’, body
           raise Exception(‘connection error’)

 
#. 将普通的任务改成队列任务 ::

    # my_send.py

    import time
    from ztq_core import async

    @async                            # 使用默认队列default
    def send(body):
           print ‘START: ‘, body
           sleep(5)
           print ‘END:’, body

    @async(queue=‘mail’)            # 使用队列mail
    def send(body):
           print ‘START2’, body
           raise Exception(‘connection error’)


#. 运行worker ::

    # 运行：bin/ztq_worker app.ini

    # app.ini 例子, 在ztq_worker 包里面有个config 目录放有app.ini 这个文件

    [server]
    host = localhost
    port = 6379
    db = 0
    alias = w01
    active_config = false
    modules = my_send                   # 所有需要import的任务模块，每个一行

    [queues]
    default= 0                          # default队列，起1个处理线程
    mail = 0, 0                         # mail队列，起2个处理线程

    [log]
    handler_file = ./ztq_worker.log
    level = ERROR

#. 运行 ::

    import ztq_core
    from my_send import send

    # 设置 Redis 连接
    ztq_core.setup_redis(‘default’, ‘localhost’,  6379, 0)

    send(‘hello, world’)

    # 动态指定queue
    send(‘hello world from mail’, ztq_queue=‘mail’)

#. 更详细的测试例子可见ztq_core包下的demo.py

使用更高级的特征
--------------------------

#. 抢占式执行 ::

    # 后插入先执行。如果任务已经在队列，会优先
    send (body, ztq_first=True) 

#. 探测任务状态 ::

    # ztq_first存在就优先, ztq_run不存在就运行
    # 返回的是"running" 代表正在运行, 是"queue" 代表正在排队
    # 如果是"error" 代表出错, 是"none" 代表这个任务不在排队，也没在执行
    ping_task(send, body, ztq_first=True, ztq_run=True)

#. 支持事务 ::

    import transaction
    ztq_core.enable_transaction(True)
    send_mail(from1, to1, body1)
    send_mail(from2, to2, body2)
    transaction.commit()
    # 也可以单独关闭事务
    send_mail(from2, to2, body2, ztq_transaction=False)

#. 定时任务 ::
    
    from ztq_core.async import async
    from ztq_core import redis_wrap
    from ztq_core.cron import has_cron, add_cron_job

    @async(queue='clock-0')
    def bgrewriteaof():
        """ 将redis的AOF文件压缩 """
        redis = redis_wrap.get_redis()
        redis.bgrewriteaof()


    # 如果队列上没有这个定时任务，就加上。自动定时压缩reids
    if not has_cron(bgrewriteaof):
         add_cron({'hour':1}, bgrewriteaof)

#. 任务串行 ::

    from ztq_core import prepare_task
    # 根据(方法，参数)生成一个任务
    callback = prepare_task(send, body)
    # 执行完 send_mail 之后队列会自动将callback 放入指定的队列
    send_mail(body, ztq_callback=callback)

#. 异常处理 ::

    from ztq_core import prepare_task

    @async(queue='mail')
    def fail_callback(return_code, return_msg):
           print return_code, return_msg

    fcallback = prepare_task(send2)

    # 如果任务 send 抛出了任何异常，都会将fcallback 放入指定队列
    send(body, ztq_fcallback=fcallback)

#. 进度回调 ::

    import ztq_worker
    @async(queue='doc2pdf')
    def doc2pdf(filename):
        ...
        # 可被进度回调函数调用
        ztq_worker.report_progress(page=2)
        ...

    from ztq_core import prepare_task
    pcallback = prepare_task(send2, body)
    doc2pdf(filename,  ztq_pcallback=pcallback)

#. 批处理 ::

    # 为提升性能，需要多个xapian索引操作，一次性提交数据库
    @async(queue=‘xapian’)
    def index(data):
        pass

    def do_commit(): 
        xapian_conn.commit()

    # 每执行20个索引任务之后，一次性提交数据库
    # 不够20个，但队列空的时候，也会提交
    register_batch_queue(‘xapian’, 20, batch_func=do_commit)

