ZTQ：Z Task Queue
===========================================
ZTQ是python语言的一个开源异步队列服务, 使用redis作为队列的存储和通讯。

和其他队列服务不同，ZTQ的设计目标是：

- 实现简单
- 容易使用
- 可靠
- 错误、拥塞时，可管理
- 容易调试
- 灵活调度，高效利用服务器

详细介绍可参看： https://github.com/everydo/ztq/raw/master/about-ztq.pptx

ZTQ是由易度云办公(http://everydo.com) 赞助开发的，在易度云查看和易度文档管理等系统中广泛使用。

主要作者和维护人:

- 徐陶哲 http://weibo.com/xutaozhe
- 潘俊勇 http://weibo.com/panjunyong

安装
--------------------
包括4个包：

1. ztq_core:   提供队列操作的底层操作API
2. ztq_worker:   队列的处理服务
3. ztq_console：队列的监控后台服务（使用Pyramid开发），这个包是可选运行的
4. ztq_demo： 一个demo示例

可直接使用标准的pip进行安装：

    pip install ztq_core
    pip install ztq_worker
    pip install ztq_console

使用
-------------------
详细的测试例子可见 ztq_demo包

1. 先定义一个普通的任务

        import time

        def send(body):
            print ‘START: ‘, body
            time.sleep(5)
            print ‘END:’, body
    
        def send2(body):
            print ‘START2’, body
            raise Exception(‘connection error’)
 
2. 将普通的任务改成队列任务

        import time
        from ztq_core import async
    
        @async                            # 使用默认队列default
        def send(body):
               print ‘START: ‘, body
               time.sleep(5)
               print ‘END:’, body
    
        @async(queue=‘mail’)            # 使用队列mail
        def send2(body):
               print ‘START2’, body
               raise Exception(‘connection error’)

3. 运行worker

   通过这个命令运行worker

        bin/ztq_worker app.ini

   下面是 app.ini 例子:

        [server]
        host = localhost
        port = 6379
        db = 0
        alias = w01
        active_config = false
        modules = ztq_demo.tasks                   # 所有需要import的任务模块，每个一行
    
        [queues]
        default= 0                          # default队列，起1个处理线程
        mail = 0, 0                         # mail队列，起2个处理线程
    
        [log]
        handler_file = ./ztq_worker.log
        level = ERROR

4. 运行

        import ztq_core
        from my_send import send
    
        # 设置 Redis 连接
        ztq_core.setup_redis(‘default’, ‘localhost’,  6379, 0)
    
        send(‘hello, world’)
    
        # 动态指定queue
        send(‘hello world from mail’, ztq_queue=‘mail’)

启动监控后台
--------------------

    bin/ztq_console app.ini

更高级的特性
--------------------------

1. 抢占式执行

   后插入先执行。如果任务已经在队列，会优先

        send (body, ztq_first=True) 

2. 探测任务状态

        ping_task(send, body, ztq_first=True, ztq_run=True)

   任务存在如下状态:

   * running: 代表正在运行, 
   * queue: 代表正在排队
   * error: 代表出错
   * none: 代表这个任务不在排队，也没在执行

   参数：

   - ztq_first：存在就优先
   - ztq_run：不存在就运行


3. 支持事务

        import transaction
        ztq_core.enable_transaction(True)
        send_mail(from1, to1, body1)
        send_mail(from2, to2, body2)
        transaction.commit()
        # 也可以单独关闭事务
        send_mail(from2, to2, body2, ztq_transaction=False)

4. 定时任务

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

5. 任务串行

        from ztq_core import prepare_task
        # 根据(方法，参数)生成一个任务
        callback = prepare_task(send, body)
        # 执行完 send_mail 之后队列会自动将callback 放入指定的队列
        send_mail(body, ztq_callback=callback)

6. 异常处理

        from ztq_core import prepare_task
    
        @async(queue='mail')
        def fail_callback(return_code, return_msg):
               print return_code, return_msg
    
        fcallback = prepare_task(send2)
    
        # 如果任务 send 抛出了任何异常，都会将fcallback 放入指定队列
        send(body, ztq_fcallback=fcallback)

7. 进度回调

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

8. 批处理

        # 为提升性能，需要多个xapian索引操作，一次性提交数据库
        @async(queue=‘xapian’)
        def index(data):
            pass
    
        def do_commit(): 
            xapian_conn.commit()
    
        # 每执行20个索引任务之后，一次性提交数据库
        # 不够20个，但队列空的时候，也会提交
        register_batch_queue(‘xapian’, 20, batch_func=do_commit)

