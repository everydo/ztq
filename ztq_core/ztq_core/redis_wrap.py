#coding:utf-8

import redis
import pickle
import sys
try:
    import json
except :
    import simplejson as json

import UserDict, UserList

ConnectionError = redis.exceptions.ConnectionError

DEFAULT_ENCODING = sys.getfilesystemencoding()
#--- System related ----------------------------------------------
SYSTEMS = {
    'default': redis.Redis(host='localhost', port=6379)
}


def setup_redis(name, host, port, db=0, **kw):
    SYSTEMS[name] = redis.Redis(host=host, port=port, db=db, **kw)

def get_redis(system='default'):
    return SYSTEMS[system]

#--- Decorators ----------------------------------------------
def get_list(name, system='default',serialized_type='json'):
    return ListFu(name, system, serialized_type=serialized_type)

def get_queue(name, system='default',serialized_type='json'):
    return QueueFu(name, system, serialized_type=serialized_type)

def get_limit_queue(name, length, system='default',serialized_type='json'):
    return LimitQueueFu(name, length, system, serialized_type=serialized_type)

def get_hash(name, system='default',serialized_type='json'):
    return HashFu(name, system, serialized_type=serialized_type)

def get_set(name, system='default',serialized_type='json'):
    return SetFu(name, system, serialized_type=serialized_type)

def get_dict(name, system='default',serialized_type='json'):
    return DictFu(name, system, serialized_type=serialized_type)

def get_key(name, system='default',serialized_type='json'):
    loads = load_method[serialized_type]
    value = get_redis(system).get(name)
    try:
        return loads(value)
    except:return value
    
def get_keys(name, system='default'):
    key_list = get_redis(system).keys(name+"*")
    for key in key_list:
        key_name = key[len(name):]
        yield key_name
    
    
def set_key(name, value, system='default',serialized_type='json'):
    dumps = dump_method[serialized_type]
    value = dumps(value)
    get_redis(system).set(name, value)

#---serialize data type----------------------------------------
def _convert_persistent_obj(obj):
    # fix json.dumps raise TypeError
    # 是persistent 对象
    if isinstance(obj, (UserDict.UserDict, dict)):
        return dict(obj)
    elif isinstance(obj, (UserList.UserList, list, set)):
        return list(obj)
    raise TypeError, '%s: %s is not JSON serializable'%(type(obj), repr(obj))

dump_method = {'json':lambda item : json.dumps(item, sort_keys=True, \
                encoding=DEFAULT_ENCODING, default=_convert_persistent_obj),
               'pickle':pickle.dumps,
               'string':str
               }
load_method = {'json':json.loads,
               'pickle':pickle.loads,
               'string':str
               }
    
#--- Data impl. ----------------------------------------------
class ListFu(object):

    def __init__(self, name, system, serialized_type='json'):
        self.name = name
        self.system = system
        self.type = serialized_type
        self.dumps = dump_method[serialized_type]
        self.loads = load_method[serialized_type]
        
    def append(self, item):
        item = self.dumps(item)
        get_redis(self.system).lpush(self.name, item)

    def extend(self, iterable):
        for item in iterable:
            self.append(item)
    
    def remove(self, value):
        value = self.dumps(value)
        get_redis(self.system).lrem(self.name, value)

    def pop(self, index=None):
        if index:
            raise ValueError('Not supported')
        serialized_data = get_redis(self.system).rpop(self.name)
        if serialized_data[1]:
            item = self.loads(serialized_data[1])
            return item
        else: return None

    def __len__(self):
        return get_redis(self.system).llen(self.name)

    def __iter__(self):
        client = get_redis(self.system)
        i = 0
        while True:
            items = client.lrange(self.name, i, i+30)
            if len(items) == 0:
                break
                #raise StopIteration
            for item in items:
                yield self.loads(item)
            i += 30

    def __getitem__(self, index):
        client = get_redis(self.system)
        value = client.lindex(self.name, index)
        return self.loads(value) if value else None

    def __getslice__(self, i, j):
        client = get_redis(self.system)
        items = client.lrange(self.name, i, j)
        for item in items:
            yield self.loads(item)

class HashFu:

    def __init__(self, name, system, serialized_type='json'):
        self.name = name
        self.system = system
        self.dumps = dump_method[serialized_type]
        self.loads = load_method[serialized_type]

    def get(self, key, default=None):
        value = get_redis(self.system).hget(self.name, key)
        try:
            return self.loads(value)
        except: return default
        
    def items(self):
        key_list = get_redis(self.system).keys(self.name+"*")
        for key in key_list:
            key_name = key[len(self.name):]

            # key_list 不是实时的数据
            # 这个任务可能已经被取走了（当监视这个队列的工作线程有多个的时候）
            value = self.get(key_name)
            if value is None: continue

            yield key_name, value

    def keys(self):
        return get_redis(self.system).hkeys(self.name) or []

    def values(self):
        _values = self.loads(get_redis(self.system).hvals(self.name))
        return _values or []

    def pop(self, key):
        pline = get_redis(self.system).pipeline()
        pline.hget(self.name, key).hdel(self.name, key)
        _value, _expire = pline.execute()
        if _expire:
            return self.loads(_value)
        else:
            #raise KeyError,'redis hasher not match the %s key\n\n'%key
            print 'redis hasher not match the %s key\n\n'%key
            return None

    def __len__(self):
        return get_redis(self.system).hlen(self.name) or 0

    def __getitem__(self, key):
        val = self.get(key)
        if not val:
            raise KeyError
        return val

    def __setitem__(self, key, value):
        value = self.dumps(value)
        return get_redis(self.system).hset(self.name, key, value)

    def __delitem__(self, key):
        get_redis(self.system).hdel(self.name, key)

    def __contains__(self, key):
        return get_redis(self.system).hexists(self.name, key)

    def update(self, new_dict, **kw):
        update = {}

        if new_dict and hasattr(new_dict, 'keys'):
            for key in new_dict:
                update[key] = self.dumps(new_dict[key])
        elif new_dict:
            for key, value in new_dict:
                update[key] = self.dumps(key)

        for key in kw:
            update[key] = self.dumps(key[key])

        if update:
            get_redis(self.system).hmset(self.name, update)

class SetFu:

    def __init__(self, name, system, serialized_type='json'):
        self.name = name
        self.system = system
        self.dumps = dump_method[serialized_type]
        self.loads = load_method[serialized_type]
        
    def add(self, item):
        item = self.dumps(item)
        get_redis(self.system).sadd(self.name, item)

    def remove(self, item):
        item = self.dumps(item)
        get_redis(self.system).srem(self.name, item)

    def pop(self, item):
        item = self.serializer.dumps(item)
        value = get_redis(self.system).spop(self.name, item)
        return self.loads(value)

    def __iter__(self):
        client = get_redis(self.system)
        for item in client.smembers(self.name):
            yield self.loads(item)

    def __len__(self):
        return len(get_redis(self.system).smembers(self.name))

    def __contains__(self, item):
        item = self.dumps(item)
        return get_redis(self.system).sismember(self.name, item)

class DictFu:
    
    def __init__(self, name, system, serialized_type='json'):
        self.name = name
        self.system = system
        self.dumps = dump_method[serialized_type]
        self.loads = load_method[serialized_type]
    
    def get(self, key, default=None):
        value = get_redis(self.system).get(self.name+key)
        try:
            return self.loads(value)
        except: return default
        
    def set(self, key, value):
        value = self.dumps(value)
        get_redis(self.system).set(self.name+key, value)
    
    def __delitem__(self, key):
        get_redis(self.system).delete(self.name+key)
    
    def __len__(self):
        listkey = get_redis(self.system).keys(self.name+"*")
        return len(listkey) or 0

    def keys(self):
        prefix_len = len(self.name)
        return [key[prefix_len:] for key in get_redis(self.system).keys(self.name + "*")]

    def items(self):
        # XXX self.get 每次都要连结redis， 这样不好
        key_list = get_redis(self.system).keys(self.name+"*")
        for key in key_list:
            key_name = key[len(self.name):]

            # key_list 不是实时的数据
            # 这个任务可能已经被取走了（当监视这个队列的工作线程有多个的时候）
            value = self.get(key_name)
            if value is None: continue

            yield key_name, value
    
    def __getitem__(self, key=''):
        val = self.get(key, None)
        if val is None:
            raise KeyError
        return val
    
    def __setitem__(self, key, value):
        self.set(key, value)
    
    def __contains__(self, key):
        return get_redis(self.system).exists(self.name+key)

class QueueFu(ListFu):

    def __init__(self, name, system, serialized_type='json'):
        super(QueueFu,self).__init__(name, system, serialized_type=serialized_type)
 
    def push(self, item, to_left=True):
        if to_left:
            self.append(item)
        else: 
            item = self.dumps(item)
            get_redis(self.system).rpush(self.name, item)
            
    def pop(self, timeout=0, from_right = True):
        """ 
            得到redis list 对象中的一个item，并把item 从 redis list 对象中删除
            from_right: 如果值为真，从redis list 对象右边读取，反之，从左边读取
            timeout: timeout 等于大于0，以阻塞式获取。timeout 小于0，直接获取返回
        """
        if from_right:
            if timeout >= 0:
                serialized_data = get_redis(self.system).brpop(self.name, timeout)
            else:
                serialized_data = get_redis(self.system).rpop(self.name)
        else:
            if timeout >= 0:
                serialized_data = get_redis(self.system).blpop(self.name, timeout)
            else:
                serialized_data = get_redis(self.system).lpop(self.name)

        if serialized_data:
            # 阻塞式获取，返回self.name, result
            if isinstance(serialized_data, (tuple, list, set)) and \
                     len(serialized_data) == 2 and serialized_data[1]:
                return self.loads(serialized_data[1])
            # 直接获取，返回 result
            else:
                return self.loads(serialized_data)

        return None
     
    def reverse(self):
        """倒序输出结果 
        """
        client = get_redis(self.system)
        length = client.llen(self.name)
        for index in xrange(length-1, -1, -1):
            item = client.lindex(self.name, index)
            yield self.loads(item)
        
class LimitQueueFu(QueueFu):
    """此队列类用于控制队列长度，主要用于日志
    """
    def __init__(self, name, length, system, serialized_type='json'):
        super(LimitQueueFu,self).__init__(name, system, serialized_type=serialized_type)
        self.length = length - 1
        
    def push(self, item):
        #QueueFu.push(self, item)
        #get_redis(self.system).ltrim(self.name, 0, self.length)

        item = self.dumps(item)
        pline = get_redis(self.system).pipeline()
        pline.lpush(self.name, item).ltrim(self.name, 0, self.length)
        pline.execute()

