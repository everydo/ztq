# encoding: utf-8
from ztq_core import async
import time

@async
def send(body):
    print 'START: ', body
    time.sleep(3)
    print 'END: ', body

@async(queue='mail')
def send_failed(body):
    print 'FAIL START:', body
    raise Exception('connection error...')

@async(queue='mail')
def failed_callback(return_code, return_msg):
    print 'FAILED CALLBACK:', return_code, return_msg

@async(queue='index')
def index(data):
    print 'INDEX:', data
    time.sleep(1)

def do_commit():
    print 'COMMITTED'

import ztq_worker
ztq_worker.register_batch_queue('index', 5, do_commit)
