#coding:utf-8
'''
测试说明:
此测试是针对redis_wrap库进行自动json编码的测试

测试结果:
Ran 5 tests in 0.036s

FAILED (failures=1)

失败原因是在对list进行remove(value)操作的时候,redis的lrem无法删除序列化后的对象,
set类型能正常remove序列化后的对象.

@author: Zay
'''
import unittest
from ztq_core import get_redis, get_list, get_hash, get_set, get_dict, setup_redis, \
get_key, set_key, get_queue

class TestRediswrap(unittest.TestCase):
    def setUp(self):
        """初始化连接redis,和初始化变量
        """
        setup_redis('default', '192.168.209.128', 6379, socket_timeout=2)
        get_redis(system='default').delete('list')
        get_redis(system='default').delete('set')
        get_redis(system='default').delete('hash')
        get_redis(system='default').delete('dict')
        get_redis(system='default').delete('kv')
        get_redis(system='default').delete('queue')
        self.message = {"hello":"grizzly"}
        
    def test_getset(self):
        """进行基本的redis 的key进行get和set的操作.
        """
        Test_key = get_key('kv',serialized_type='json')
        self.assertEqual(Test_key,None)
        
        set_key('kv',self.message)
        
        Test_key = get_key('kv',serialized_type='json')
        self.assertEqual(Test_key,self.message)
        
    def test_dict(self):
        """测试redis_wrap的dict类型的操作
        """
        Test_dict = get_dict('dict',serialized_type='json')
        
        Test_dict['id'] = self.message
        self.assertEqual(self.message, Test_dict['id'])
        
        for k,v in Test_dict.items():
            self.assertEqual(k, 'id')
            self.assertEqual(v, self.message)
        
        del Test_dict['id']
        self.assertNotEqual(self.message,Test_dict.get('id'))
        
    def test_hash(self):
        """测试redis_wrap的 hash类型的操作
        """
        Test_dict = get_hash('hash',serialized_type='json')
        
        Test_dict['id'] = self.message
        self.assertEqual(self.message, Test_dict['id'])
        
        del Test_dict['id']
        self.assertNotEqual(self.message,Test_dict.get('id'))        
        
    def test_list(self):
        """进行redis_wrap的list的基本操作
        """
        Test_list = get_list('list',serialized_type='json')
        
        Test_list.append(self.message)
        self.assertEqual( len(Test_list),1)
    
        for item in Test_list:
            self.assertEqual(self.message, item)
            
        #这一步失败原因是redis的lrem方法有无法删除序列化后的数据
        Test_list.remove(self.message)
        self.assertEqual( len(Test_list),0)

    def test_set(self):
        """进行对redis_wrap的set类型的基本操作
        """
        Test_set = get_set('set',serialized_type='json')
        Test_set.add(self.message)
        
        for item in Test_set:
            self.assertEqual( item,self.message)
            
        Test_set.remove(self.message)
        self.assertEqual( len(Test_set),0)

    def test_queue(self):
        """进行redis_wrap的queue的基本操作
        """
        Test_queue = get_queue('queue',serialized_type='json')
        
        Test_queue.push(self.message)
        self.assertEqual( len(Test_queue),1)
    
        for item in Test_queue:
            self.assertEqual(self.message, item)
            
        #这一步失败原因是redis的lrem方法有无法删除数据
        Test_queue.remove(self.message)
        self.assertEqual( len(Test_queue),0)
    #===========================================================================
    # 
    #    message = Test_queue.pop(timeout= 1)
    #    self.assertEqual(self.message, message)
    #    self.assertEqual(len(Test_queue),0)
    #===========================================================================
        
if __name__ == '__main__':
    unittest.main()
