# encoding: utf-8
#  my_send.py
import time
import ztq_core
import transaction
from ztq_demo.tasks import send, send_failed, failed_callback

ztq_core.setup_redis('default','localhost', 6379, 3)

#send('hello, world 1')
#send('hello, world 2')
#send('hello, world 3')



#send('hello, world 3', ztq_queue='mail')



#ztq_core.enable_transaction(True)
#send('send 1')
#send('send 2')
#print 'send, waitting for commit'
#time.sleep(5)
#transaction.commit()
#print 'committed'




#ztq_core.enable_transaction(True)
#send('transaction msg show later')
#send('no transaction msg show first', ztq_transaction=False)
#transaction.commit()


#ztq_core.enable_transaction(False)
#callback = ztq_core.prepare_task(send, 'yes, callback!!')
#send('see callback?', ztq_callback=callback)

#fc = ztq_core.prepare_task(failed_callback)
#send_failed('send a failed msg, see failed callback?', ztq_fcallback=fc)

