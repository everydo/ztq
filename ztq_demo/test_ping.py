import time
import ztq_core
from ztq_demo.tasks import send

ztq_core.setup_redis('default','localhost', 6379, 3)

send('hello, world 1')
send('hello, world 2')

print 'hello, world 1:'
import pdb; pdb.set_trace()
print ztq_core.ping_task(send, 'hello, world 1')
print 'hello, world 2:'
print ztq_core.ping_task(send, 'hello, world 2')
