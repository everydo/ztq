#coding:utf-8
from async import async
import redis_wrap
from cron import has_cron, add_cron

@async(queue='clock-0')
def bgrewriteaof():
    """ 将redis的AOF文件压缩 """
    redis = redis_wrap.get_redis()
    redis.bgrewriteaof()

def set_bgrewriteaof():
    # 自动定时压缩reids
    if not has_cron(bgrewriteaof):
        add_cron({'hour':1}, bgrewriteaof)

