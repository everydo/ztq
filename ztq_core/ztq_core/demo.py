# encoding: utf-8
#  my_send.py
from ztq_core import async
import ztq_worker
import time

@async(queue='mail')
def send(body):
    print 'START: ', body
    time.sleep(5)
    print 'END: ', body

@async(queue='mail')
def send2(body):
    print 'START2 … ', body
    raise Exception('connection error')

@async(queue='mail')
def call_process(filename):
    print 'call process:', filename
    ztq_worker.report_job(12323, comment=filename)
    time.sleep(20)

@async(queue='mail')
def fail_callback(return_code, return_msg):
    print 'failed, noe in failed callback'
    print return_code, return_msg

def test():
    import ztq_core
    import transaction

    from ztq_core import demo

    ztq_core.setup_redis('default','localhost', 6379, 1)

    demo.send('*' * 40, ztq_queue='mail')

    demo.send('transaction will on', ztq_queue='mail')
    ztq_core.enable_transaction(True)

    demo.send('transaction msg show later')
    demo.send('no transaction msg show first', ztq_transaction=False)
    time.sleep(5)
    transaction.commit()
    
    ztq_core.enable_transaction(False)

    demo.send('transaction off')
    callback = ztq_core.prepare_task(demo.send, 'yes, callback!!')
    demo.send('see callback?', ztq_callback=callback)

    ff = ztq_core.prepare_task(demo.fail_callback)
    demo.send2('send a failed msg, see failed callback?', ztq_fcallback=ff)

    call_process('saa.exe')

if __name__ == '__main__':
    test()
