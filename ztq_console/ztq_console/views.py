#coding:utf-8
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.events import subscriber
from pyramid.interfaces import IBeforeRender
from pyramid.url import static_url, resource_url, route_url
from pyramid.threadlocal import get_current_request
import time
import ztq_core
import utils 
import urllib

MENU_CONFIG = {'title':u'ZTQ队列监控后台',
               'links':[('/workerstatus', u'工作状态'),
                     ('/taskqueues',u'工作队列'),
                     ('/errorlog',u'错误清单'),
                     ('/workerlog', u'工作历史'),
                     ('/syslog', u'系统日志'),
                     ]
        }

@view_config(renderer='mainpage.html')
def main_view(request):
    """后台管理首页
    """  
    return MENU_CONFIG

@view_config(name='top.html', renderer='top.html')
def top_view(request):
    """后台管理首页
    """  
    return MENU_CONFIG

@view_config(name='menu.html', renderer='menu.html')
def menu_view(request):
    """初始化菜单
    """
    return MENU_CONFIG

@view_config(name='workerstatus', renderer='worker.html')
def workers_view(request):
    """后台管理首页
    传出参数:worker的相关信息,各个队列的工作情况
    """
    
    workers = utils.get_worker_list()    
    return {'workers':workers}  
    
@view_config(name='syslog')
@view_config(name='workerlog')
@view_config(name='errorlog')
def route_main(request):
    route_name = request.view_name
    return HTTPFound(location=request.route_url(route_name, page=1))

#--------------日志信息--------------------------------    
@view_config(route_name='syslog', renderer='syslog.html')
def sys_log_view(request):
    """查看系统日志情况
    """
    page = request.matchdict.get('page', 1)
    page = int(page) or 1

    return pageination(utils.get_sys_log, page, 'sys_log')

#--------------转换历史--------------------------------    
@view_config(route_name='workerlog', renderer='workerlog.html')
def worker_log_view(request):
    """查看转换日志
    """
    page = request.matchdict.get('page', 1)
    page = int(page) or 1

    return pageination(utils.get_worker_log, page, 'worker_log')

#--------------调度管理--------------------------------
def config_worker(request):
    """对worker进行配置管理
    """
    url_action = request.params.get('action','')

    dispatcher_config = ztq_core.get_dispatcher_config()
    worker_weight = dispatcher_config['worker_weight']
    # 获取用户请求操作
    worker_id = request.matchdict['id']
    # 根据操作类型进行权重调整,
    if url_action == 'stop_worker': 
        #停止worker
        worker_weight[worker_id] = 0
    elif url_action == 'enable': 
        #启用worker
        worker_weight[worker_id] = 5
    elif url_action == 'worker_down' : 
        #降低worker权重
        worker_weight[worker_id] -= 1
        if worker_weight[worker_id] < 1: worker_weight[worker_id] = 1
    elif url_action == 'worker_up' : 
        #提升worker权重
        worker_weight[worker_id] += 1
        if worker_weight[worker_id] >10: worker_weight[worker_id] = 10
    elif url_action == 'delete': 
        #删除还没启用的worker,删除操作不会导致调度配置更新
        if worker_id in worker_weight: # 没有启用的情况
            worker_weight.pop(worker_id)
        workers_dict = ztq_core.get_worker_state()
        del workers_dict[worker_id]
        worker_job = ztq_core.get_job_state(worker_id)
        for job_name, job_status in worker_job.items():
            del worker_job[job_name]
        ztq_core.set_dispatcher_config(dispatcher_config)
        return HTTPFound(location = '/workerstatus')
    elif url_action == 'update':
        # 发报告指令到各命令队列让worker报告自身状态
        worker_list = ztq_core.get_all_worker()
        for worker_name in worker_list:
            if worker_name == worker_id:
                utils.send_command(worker_name, 'report')
                time.sleep(1)
                return HTTPFound(location = '/workerstatus')
    # 更新调度策略并进行调度        
    ztq_core.set_dispatcher_config(dispatcher_config)
    utils.dispatch()
    return HTTPFound(location = '/workerstatus')

def stop_working_job(request):
    """停止正在进行中的转换的工作
    """
    kill_command =   {
     'command':'kill',
     'timestamp':int(time.time()),
     'pid':'',
     }
    # 获取url操作
    worker_id = request.matchdict['id']
    thread_pid = request.matchdict['pid']
    # pid为-1则不能杀
    if thread_pid == -1: return HTTPFound(location = '/workerstatus')
    else: kill_command['pid'] = thread_pid
    cmd_queue = ztq_core.get_command_queue(worker_id)
    # 避免同时发送多条结束命令
    if cmd_queue:
        for command in cmd_queue:
            if command.get('pid', None) == kill_command['pid']:    
                return HTTPFound(location = '/workerstatus')          
    cmd_queue.push(kill_command)  
    return HTTPFound(location = '/workerstatus')


#--------------查看队列详情-------------------------------
@view_config(name='taskqueues', renderer='queues.html')
def task_queues(request):
    """查看转换队列运行状态
    传出参数:所有原子队列的运行转换
    """
    task_job_length = 0
    error_job_length = 0
    # 计算原子队列,原始队列和错误队列的总长度
    queues_list = ztq_core.get_queue_config()
    for queue_name, queue_config in queues_list.items():
        task_job_length += len(ztq_core.get_task_queue(queue_name))
        error_job_length += len(ztq_core.get_error_queue(queue_name))
    task_queues = utils.get_taskqueues_list()
    
    return {'task_queues':task_queues,
            'task_job_length':task_job_length,
            'error_job_length':error_job_length, }
        
@view_config(route_name='taskqueue',renderer='jobs.html')
def taskqueue(request):
    """用于查看某个队列的详细信息和运行情况
    """
    queue_id = request.matchdict['id']
    jobs = utils.get_queues_jobs(queue_id)
    return {'jobs':jobs, 'queue_name':queue_id}    

def config_queue(request):
    """管理队列权重,提升队列权重或降低队列权重
       传入参数:http://server/taskqueues/q01/config?action=queue_down
    """
    queue_id = request.matchdict['id']
    url_action = request.params.get('action','')
    dispatcher_config = ztq_core.get_dispatcher_config()
    queue_weight = dispatcher_config['queue_weight']

    # 根据操作类型进行权重调整,
    if url_action == 'queue_down' : 
        queue_weight[queue_id] -= 1
        # 队列权重最少为1
        if queue_weight[queue_id] < 0: queue_weight[queue_id] = 0
        # 更新调度策略并进行调度
        ztq_core.set_dispatcher_config(dispatcher_config)
        utils.dispatch()
    elif url_action == 'queue_up' : 
        queue_weight[queue_id] += 1
        if queue_weight[queue_id] > 10: queue_weight[queue_id] = 10
        # 更新调度策略并进行调度
        ztq_core.set_dispatcher_config(dispatcher_config)
        utils.dispatch()
    elif url_action == 'from_right' : 
        utils.dispatch_single_queue(queue_id, from_right=True)
    elif url_action == 'from_left' : 
        utils.dispatch_single_queue(queue_id, from_right=False)   
    return HTTPFound(location = '/taskqueues') 
  
@view_config(route_name='taskqueue_action')
def task_jobs_handler(request):
    """将任务调整到队头或者队尾
    传入参数:http://server/taskqueues/q01/job?action=high_priority&hash_id={{job_hash_id}}
    """
    valid_action = ('high_priority','low_priority', 'delete')
    queue_name  = request.matchdict['id']
    url_action = request.params.get('action','')
    job_hash_id = urllib.unquote(request.params.get('hash_id').encode('utf8'))
    if url_action in valid_action:
        if url_action == 'high_priority':
            job_queue = ztq_core.get_task_queue(queue_name)
            job_queue.remove(job_hash_id)
            job_queue.push(job_hash_id, to_left=False)
        elif url_action == 'low_priority':
            job_queue = ztq_core.get_task_queue(queue_name)
            job_queue.remove(job_hash_id)
            job_queue.push(job_hash_id)
        elif url_action == 'delete':
            job_queue = ztq_core.get_task_queue(queue_name)
            job_queue.remove(job_hash_id)
            job_hash = ztq_core.get_task_hash(queue_name)
            job_hash.pop(job_hash_id)
        return HTTPFound(location = '/taskqueues/'+queue_name)
    else: 
        return Response('Invalid request')  

#--------------错误处理--------------------------------    
@view_config(route_name='errorlog', renderer='errorlog.html')
def error_queue_detail(request):
    """用于查看所有错误队列的详细信息和运行情况
    error_queue = 'ztq:queue:error:' + queue_name
    """
    page = request.matchdict.get('page', 1)
    page = int(page) or 1
    return pageination(utils.get_all_error_jobs, page, 'error_jobs')

@view_config(route_name='errorqueue', renderer='errorlog.html')
def errorqueue(request):
    """用于查看单个错误队列的详细信息和运行情况
    """
    error_queue_id = request.matchdict['id']
    page = request.matchdict.get('page', 1)
    page = int(page) or 1
    return pageination(utils.get_error_queue, page, 
                        'error_jobs', error_queue_id)

def error_jobs_handler(request):
    """从错误队列中移除或重做某个失败的转换
       传入参数:http://server/errorqueues/q01/job?action=remove{redo}&hash_id={{hashid}}
    """
    valid_action = ('remove','redo')
    queue_id = request.matchdict['id']
    url_action = request.params.get('action','')
    hash_id = urllib.unquote(request.params.get('hash_id').encode('utf8'))
    if url_action in valid_action:
        if url_action == 'remove':
            ztq_core.pop_error(queue_id, hash_id)
        elif url_action == 'redo':
            task = ztq_core.pop_error(queue_id, hash_id)
            task['runtime'] = {'queue':queue_id, 'create':int(time.time())}
            ztq_core.push_runtime_task(queue_id, task)
        return HTTPFound(location = '/errorlog')
    else: return Response('Invalid request')

@view_config(route_name='redo_all_error_for_queue')
def redo_all_error_for_queue(request):    
    """重做这个错误队列所有的任务
    """
    queue_id = request.matchdict['id']

    while 1:
        error_task = ztq_core.pop_error(queue_id, timeout=-1)
        if error_task is None:
            break
        error_task['runtime'] = {'queue':queue_id, 'create':int(time.time())}
        ztq_core.push_runtime_task(queue_id, error_task)

    return HTTPFound(location = '/taskqueues')

@view_config(route_name='del_all_error_for_queue')
def del_all_error_for_queue(request):    
    """删除这个错误队列所有的任务
    """
    queue_id = request.matchdict['id']

    error_hash = ztq_core.get_error_hash(queue_id)
    error_queue = ztq_core.get_error_queue(queue_id)

    client = ztq_core.get_redis()
    client.delete(error_queue.name)
    client.delete(error_hash.name)

    return HTTPFound(location = '/taskqueues')

#-------------------------------------------------------------
@subscriber(IBeforeRender)
def add_globals(event):
    '''Add *context_url* and *static_url* functions to the template
    renderer global namespace for easy generation of url's within
    templates.
    '''
    request = event['request']
    def context_url(s, context=None,request=request):
        if context is None:
            context = request.context
        url = resource_url(context,request)
        if not url.endswith('/'):
            url += '/'
        return url + s
    def gen_url(route_name=None, request=request, **kw):
        if not route_name:
            local_request = get_current_request()
            route_name = local_request.matched_route.name
        url = route_url(route_name, request, **kw)
        return url
    event['gen_url'] = gen_url
    event['context_url'] = context_url
    event['static_url'] = lambda x: static_url(x, request)

def pageination(gen_func, page, resource_name, *args):
    sindex = ( page - 1 ) * 20
    eindex = page * 20
    fpage = page - 1
    npage = page + 1
    resource = gen_func(*args, sindex=sindex, eindex=eindex-1)
    return {resource_name:resource,
            'sindex':str(sindex + 1),
            'eindex':str(eindex),
            'fpage':fpage,
            'npage':npage,
            } 

