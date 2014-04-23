#coding:utf-8
from redis_wrap import get_set, get_key, set_key, \
get_queue, get_dict, get_keys, get_limit_queue, get_hash

def get_all_task_queue():
    """返回所有原子队列的key
            返回类型:list
    """
    task_queue = "ztq:queue:task:"
    return get_keys(task_queue)

def get_all_error_queue():
    """返回所有原子队列的key
            返回类型:list
    """
    task_queue = "ztq:queue:error:"
    return get_keys(task_queue)

def get_task_hash(queue_name):
    """ 得到 一个 task_md5 -> task 的字典对象 """
    return get_hash('ztq:hash:task:' + queue_name)

def get_task_set(queue_name, serialized_type='json'):
    """ 得到 一个 task_md5 -> task 的字典对象 """
    return get_set('ztq:set:task:' + queue_name, serialized_type=serialized_type)

def get_task_queue(queue_name):
    """根据传入参数queue_name

    {"func":'transform',
     'args':(),
     'kw':{'path':'c:\\abc.doc',              #源文件路径
      'mime':'application/ms-word',      #源文件类型
      'transform':[
         {'path':'d:\\abc.html',  
          'mime':'text/html',
          'callback':'http://xxx.com/asss'

          'transform':[
             {'path':'d:\\abc.txt',
              'mime':'text/plain',
              'transform':[]
             }, # 转换子文件放在同一文件夹中
          ]}]},

     'callback':callback,            # 全部完成调用方法
     'callback_args':callback_args,  # 全部完成的调用参数
     'callback_kw':callback_kw,

     'pcallback':callback, # progress callback 部分完成的调用
     'pcallback_args':callback_args, # 部分完成的调用参数
     'pcallback_kw':callback_kw,     # 部分完成调用参数

     'fcallback':callback,            # 失败调用方法
     'fcallback_args':callback_args,  # 失败的调用参数
     'fcallback_kw':callback_kw,

     "runtime":{ # 队列运行相关信息
       'created':12323423   # 进入队列时间
     }
    }
    """
    #ListFu
    atom_queue = "ztq:queue:task:" + queue_name
    return get_queue(atom_queue, serialized_type='string')

def get_command_queue(name):
    """ 同步配置、状态报告、杀死转换线程
    
       要求同步worker配置
    {
     'command':'updateworker',
     'timestamp':''
                   }
        要求同步转换器线程驱动
    {
     'command':'updatedriver',
     'timestamp':''
                   }
                   
        要求worker报告整体工作状态::

     {
     'command':'report',
     'timestamp': 
     }
        后台杀一个转换进程（可能卡死）::
     {
     'command':'kill',
     'timestamp':
     'pid':'2121',
     }
    
    用户取消一个转换进程，和杀死类似，不应该进入错误队列，日志也需要说明是取消::
     {
     'command':'cancel',
     'timestamp':
     'pid':'2121',
     }
    """
    command_queue = 'ztq:queue:command:'+name
    return get_queue(command_queue)

def get_work_log_queue():
    """ json格式为::

     {'func':'transform',
      'kw':{ ... # 和前面task_queue相同
         },
      "runtime":{ # 队列运行相关信息
         'created':12323423   #进入原始队列时间
         'queue':'q01'  # 是在哪个原子原子队列
         'start':123213123    #转换开始时间
         'end':123213123    #转换结束时间
         'worker':'w01', # 转换器名
         'thread':'131231', # 
         'return':-1, # 返回的错误代号, 0表示成功 
         'reason':'失败原因' # 详细的原因
       }
      }
    """
    work__log_queue = "ztq:queue:worker_log"
    return get_limit_queue(work__log_queue, 200)

def get_error_hash(queue_name, system='default'):
    """ json格式和work_log相同 """
    error_queue = 'ztq:hash:error:' + queue_name
    return get_hash(error_queue, system=system)

def get_error_queue(queue_name, system='default'):
    """ json格式和work_log相同 """
    error_queue = 'ztq:queue:error:' + queue_name
    return get_queue(error_queue, system=system, serialized_type='string')

def get_buffer_queue(queue_name, system='default'):
    """ json格式和work_log相同 """
    buffer_queue = 'ztq:queue:buffer:' + queue_name
    return get_queue(buffer_queue, system=system)

def get_system_log_queue():
    """
    Json格式为:
    {'alias':'w01'
     'host':'192.168.1.100'
     'timestamp':123213123
     'type': 'reboot' or 'shutdown' or 'power' 三个值中其中一个
    }
    """
    system__log_queue ='ztq:queue:system_log'
    return get_limit_queue(system__log_queue, 200)

def get_callback_queue():
    callback_queue='ztq:queue:callback'
    return get_queue(callback_queue)

# state -------------------------------------------------------------------
def get_all_worker():
    """返回正在运行中的转换器列表
            返回类似:list
    """
    prefix = 'ztq:state:worker:'
    return get_keys(prefix)

def get_worker_state():
    """ transformer在如下2种状况下会，会由指令线程上报转换器的状态::

    - 启动的时候
    - 有指令要求

        在redis中的存放格式为::

      {'ip':'192.168.1.1',
       'cpu_style':'Dural Xommm 1G',
       'cpu_percent':'30%',
       'mem_total':'2G',
       'mem_percent':'60%',
       'started':1231231231,
       'timestamp':12312312,
       'tracebacks':'全部线程的traceback信息，用于死锁检查',
      }
        转换器状态信息，主要用于监控转换器是否良性工作，会在监控界面中显示。
    """
    prefix = 'ztq:state:worker:'
    return get_dict(prefix)

def get_job_state(worker_job_name):
    """ 转换器w01，第0号转换线程的当前转换任务信息

    - 每次开始转换，需要记录转换的信息
    - 每次结束的时候，需要清空

    json格式为::
    
     {'func':'transform',
      'kw':{ ... # 和上面task_queue相同
         },
      'runtime':{... # 和上面work_log相同
       }
      'process':{
          'pid': 212,  # -1 表示不能杀
          'start':131231,
          'comment':'d:\ssd.pdf'
         }
      }
    """
    prefix = 'ztq:state:job:%s:' % worker_job_name
    return get_dict(prefix)

def get_queue_config():
    """记录queue的基本信息
    {'title':'sys_cron-0',  #可选
     'tags':(['sys_cron']),  #可选
    }             #可选
    """
    prefix = 'ztq:config:queue:'
    return get_dict(prefix)

def get_worker_config():
    """ 配置工作线程：处理哪些队列，几个线程，间隔时间::
    {'q01':[{ 'interval':5,  # 间隔时间
              'from_right':True, }],  # 队列处理的方向，左（l）或者右（r） 
     'q02':[{'interval':5, 'from_right':False},
            {'interval':3, 'from_right':True}],
    }
    """
    prefix = 'ztq:config:worker:'
    return get_dict(prefix)

def get_driver_config():
    """
    TODO:消息格式
    """
    prefix = 'ztq:config:driver:'
    return get_dict(prefix)

def get_cron_set():
    """ 定时任务list
    TODO
    """
    return get_set('ztq:set:cron')
  
