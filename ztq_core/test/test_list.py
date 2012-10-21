'''
Created on 2011-4-18

@author: Zay
'''
from ztq_core import get_redis, get_list, get_hash, get_set, get_dict, setup_redis, \
get_key, set_key, get_queue

def main():
        setup_redis('default', '192.168.209.128', 6380)
        get_redis(system='default').delete('list')
        message = 'hello'
        
        Test_list = get_list('list',serialized_type='string')
        Test_list.append(message)
        
        #Test_list.remove(message)
        
        print get_redis(system='default').lrem('list', 0, 'hello')
        
        Test_set = get_set('set',serialized_type='string')
        Test_set.add(message)
        print get_redis(system='default').srem('set', 'hello')
        
        
if __name__ == '__main__':
    main()
