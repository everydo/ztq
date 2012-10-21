#coding:utf-8

from paste.httpserver import serve
import sys,os
sys.path.insert(0, os.path.abspath('../'))
sys.path.append('E:\\workspace\\Everydo_DBank\\src\\fts\\ztq_core')

if __name__ == '__main__':
    # For Debug
    from ztq_console import main
    app = main('test')
    serve(app, host='0.0.0.0', port=9013)

