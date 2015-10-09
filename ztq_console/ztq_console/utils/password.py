#coding:utf-8
from ConfigParser import ConfigParser, RawConfigParser
import sys
import os

def get_password():
    cf = ConfigParser()
    cf.read(sys.argv[1])
    password_path = cf.get('password_path', 'password_path')
    cf.read(password_path)
    return cf.get('password', 'password')

def modify_password(new_password):
    cf = ConfigParser()
    cf.read(sys.argv[1])
    password_path = cf.get('password_path', 'password_path')
    if os.path.exists(password_path):
        passwd_txt = ConfigParser()
        passwd_txt.read(password_path)
    else:
        passwd_txt = RawConfigParser()
        passwd_txt.add_section('password') 

    passwd_txt.set('password', 'password', new_password)
    with open(password_path, 'w') as new_password:
        passwd_txt.write(new_password)
