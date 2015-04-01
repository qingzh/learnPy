#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author: simpleqing@gmail.com
@version
@desc: calculation of running time
@date: 20150401
"""

import logging
import sys

from time import time

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def calculation_time(is_debug):
    def run_func(func):
        def func_wrapper(*args, **kwargs):
            if is_debug:
                begin = time()
                func(*args, **kwargs)
                logging.info( "\n  Function [{}] finished in {:.10f}s".format(func.__name__, time() - begin))
            else:
                func(*args, **kwargs)
        return func_wrapper
    return run_func

def func(name):
    print "hello world, %s" % name
    for i in xrange(10000):
        i ** 3

def test():
    func('test')

@calculation_time(True)
def test2():
    func('test2')

@calculation_time(False)
def test3():
    func('test3')

if __name__ == "__main__":
    test()
    test2()
    test3()