# encoding: utf-8
#  my_send.py
import time
import ztq_core
import transaction
from ztq_demo.tasks import send

ztq_core.setup_redis('default','localhost', 6379, 3)

ztq_core.enable_transaction(True)

send('transaction send 1')
send('transaction send 2')

send('no transaction msg show first', ztq_transaction=False)

print 'send, waitting for commit'
time.sleep(5)

transaction.commit()
print 'committed'

