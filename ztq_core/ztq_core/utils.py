#coding:utf-8
from async import async
import redis_wrap
import urllib2
from cron import has_cron, add_cron

@async(queue='clock')
def bgrewriteaof():
    """ 将redis的AOF文件压缩 """
    redis = redis_wrap.get_redis()
    redis.bgrewriteaof()

def set_bgrewriteaof():
    # 自动定时压缩reids
    if not has_cron(bgrewriteaof):
        add_cron({'hour':1}, bgrewriteaof)

@async(queue='urlopen')
def async_urlopen(url, params=None, timeout=120):
    try:
        # 将unicode转换成utf8
        urllib2.urlopen(url.encode('utf-8'), params, timeout=timeout)
    except IOError:
        raise IOError('Could not connected to %s' % url)

