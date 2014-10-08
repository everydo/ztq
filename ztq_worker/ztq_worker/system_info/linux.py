#!/usr/bin/env python
# encoding: utf-8

from __future__ import with_statement 
import subprocess as sp
import psutil

def get_cpu_usage():
    cpu_usage = psutil.cpu_percent()

    return '%.1f%%'%cpu_usage

def get_mem_usage():
    with open('/proc/meminfo') as mem_info:
        mem_total = mem_info.readline()
        mem_free = mem_info.readline()
        mem_buff = mem_info.readline()
        # 部分操作系统内核会MemAvailable一行，所以Buffers应该再取下一行文本来提取读书。
        if not mem_buff.startswith('Buffers'):
            mem_buff = mem_info.readline()

        mem_cached  = mem_info.readline()

    mem_total = int(mem_total.split(':', 1)[1].split()[0])
    mem_free = int(mem_free.split(':', 1)[1].split()[0])
    mem_buff = int(mem_buff.split(':', 1)[1].split()[0])
    mem_cached = int(mem_cached.split(':', 1)[1].split()[0])

    mem_usage = mem_total - (mem_free + mem_buff + mem_cached)
    mem_usage = 1.0 * 100 * mem_usage / mem_total

    return ( '%.1f%%'%mem_usage, '%dM'%(mem_total/1024) ) 

_CPU_STYLE = None
def get_cpu_style():
    global _CPU_STYLE
    if _CPU_STYLE is None:
        popen = sp.Popen('cat /proc/cpuinfo  | grep "model name" | head -n 1', stdout=sp.PIPE, shell=True)
        popen.wait()
        result = popen.stdout.read()
        _CPU_STYLE = result.split(':', 1)[1].strip()
    return _CPU_STYLE

_IP_ADDRESS = None
def get_ip():
    def get_ip_address(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])

    global _IP_ADDRESS
    if _IP_ADDRESS is None:
        import socket, fcntl, struct
        popen = sp.Popen("ifconfig -s | cut -d ' ' -f 1", stdout=sp.PIPE, shell=True)
        popen.wait()
        result = popen.stdout.read()
        for iface_name in result.split():
            if iface_name in ('Iface', 'lo'):
                continue
            try:
                _IP_ADDRESS = get_ip_address(iface_name)
            except:
                pass
            else:
                break
        if _IP_ADDRESS is None:
            _IP_ADDRESS = '127.0.0.1'

    return _IP_ADDRESS

if __name__ == '__main__':
    print 'cpu style: %s' % get_cpu_style()
    print 'cpu usage: %s' % get_cpu_usage()
    print 'memory usage: %s, memory total: %s' % get_mem_usage()
    print 'local ip addrs: %s'%get_ip()
    
