# encoding: utf-8
#  my_send.py
import time
import ztq_core
import transaction
from ztq_demo.tasks import send, send_failed, failed_callback

ztq_core.setup_redis('default','localhost', 6379, 3)

callback = ztq_core.prepare_task(send, 'succeed!', ztq_queue='mail')
fcallback = ztq_core.prepare_task(failed_callback)

send('send a good msg, see what?', 
		ztq_queue= 'mail',
		ztq_callback=callback,
		ztq_fcallback=fcallback)

send_failed('send a failed msg, see what?', 
		ztq_callback=callback,
		ztq_fcallback=fcallback)

