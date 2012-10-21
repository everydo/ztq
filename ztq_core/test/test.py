#coding:utf-8
import unittest


import ztq_core

def echo():
    print 'hello'

class TestftsModel(unittest.TestCase):
    def setUp(self):
        ztq_core.setup_redis('default', '192.168.209.128', 6379)
        self.testmessage = {'test':'test'}
        
    def testJsonList(self):    
        """Test queue connect
        """
        self.queue = ztq_core.get_task_queue('q01')
        self.queue.append(self.testmessage)
        revmessage = self.queue.pop()
        self.assertEqual(revmessage,self.testmessage)
    
    def _testRegister(self):
        """测试JobThread
        """
        ztq_core.task.register(echo)
        ztq_core.task.task_push(u'foo:echo', 'aaa', 'bb', c='bar') 
        job_thread = ztq_core.task.JobThread('foo')
        job_thread.start()
        
if __name__ == '__main__':
    unittest.main()
