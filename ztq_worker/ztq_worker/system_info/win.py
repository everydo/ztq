#!/usr/bin/env python
import subprocess as sp
import urllib
from os import path

LOCAL_DIR = path.dirname(path.realpath(__file__))

def get_cpu_usage():
    vbs_file = 'get_cpu_usage.vbs'
    vbs_path = path.join(LOCAL_DIR, vbs_file)
    popen = sp.Popen('cscript /nologo %s'%vbs_path, stdout=sp.PIPE, shell=True)
    popen.wait()
    result = popen.stdout.read()
    return '%s%%'%result.strip()

def get_mem_usage():
    vbs_file = 'get_mem_usage.vbs'
    vbs_path = path.join(LOCAL_DIR, vbs_file)
    popen = sp.Popen('cscript /nologo %s'%vbs_path, stdout=sp.PIPE, shell=True)
    popen.wait()
    result = popen.stdout.read()
    mem_total, mem_usage, mem_percent = result.split()
    return ( '%s%%'%mem_percent, '%sM'%mem_total ) 

_CPU_STYLE = None
def get_cpu_style():
    global _CPU_STYLE
    if _CPU_STYLE is None:
        vbs_file = 'get_cpu_style.vbs'
        vbs_path = path.join(LOCAL_DIR, vbs_file)
        popen = sp.Popen('cscript /nologo %s'%vbs_path, stdout=sp.PIPE, shell=True)
        popen.wait()
        result = popen.stdout.read()
        cpu_style = '%s'%result.strip()

        try:
            cpu_style = cpu_style.decode('gb18030')
        except UnicodeDecodeError:
            cpu_style = cpu_style.decode('utf8')

        _CPU_STYLE = cpu_style.encode('utf8')
            
    return _CPU_STYLE

def get_ip():
    return urllib.thishost()

if __name__ == '__main__':
    print 'cpu style: %s' % get_cpu_style()
    print 'cpu usage: %s' % get_cpu_usage()
    print 'memory usage: %s, memory total: %s' % get_mem_usage()
    print 'local ip addrs: %s'%get_ip()
