import time
import ztq_core
from ztq_demo.tasks import send

ztq_core.setup_redis('default','localhost', 6379, 3)

send('hello, world 1')
send('hello, world 2')
send('hello, world 3')

send('hello, world 4', ztq_queue='mail')
