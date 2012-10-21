# encoding: utf-8
#  my_send.py
import time
import ztq_core
from ztq_demo.tasks import index

ztq_core.setup_redis('default','localhost', 6379, 3)

index('only one')

time.sleep(3)

for i in range(8):
   index('data %d' % i)
