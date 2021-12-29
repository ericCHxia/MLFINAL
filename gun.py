import os 
import gevent.monkey
gevent.monkey.patch_all()
import multiprocessing

bind = "0.0.0.0:5000" 
# 启动进程数量
workers = multiprocessing.cpu_count() * 2 +1
worker_class = 'gevent'
threads = 20
preload_app = True
reload = True
x_forwarded_for_header = 'X_FORWARDED-FOR'