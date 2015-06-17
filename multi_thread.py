# -*- coding: utf-8 -*-
import threading
import time


def f(i):
    print threading.current_thread().name, ' [START]'
    time.sleep(i)
    print threading.current_thread().name, ' [END]'

func_thread = lambda x: threading.Thread(target=f, name=x, args=(x,))
threads = map(func_thread, [5, 8, 12, 9])
# the whole program will wait for the alive non-daemon threads
daemonic = False
map(lambda x: x.setDaemon(daemonic), threads)
map(lambda x: x.start(), threads)
map(lambda x: x.join(), threads)
