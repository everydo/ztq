# -*- encoding: utf-8 -*-
import sys

if sys.platform.startswith('win'):
    from win import get_cpu_style, get_cpu_usage, get_mem_usage, get_ip
else:
    from linux import get_cpu_style, get_cpu_usage, get_mem_usage, get_ip
