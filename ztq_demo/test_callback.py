# encoding: utf-8
#  my_send.py
import time
import ztq_core
import transaction
from ztq_demo.tasks import send

ztq_core.setup_redis('default','localhost', 6379, 3)

callback = ztq_core.prepare_task(send, 'yes, callback!!')
send('see callback?', ztq_callback=callback)

