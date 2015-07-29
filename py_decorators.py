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


class C(object):

    def func(self, n):
        print 'func', n
        return n * 2


def dec(func):
    def wrapper(*args, **kwargs):
        print 'dec'
        return func(*args, **kwargs)
    return wrapper


def new_dec(func):
    def wrapper(*args, **kwargs):
        print 'new dec'
        return func(*args, **kwargs) * 5
    return wrapper

'''
C.new_func = dec(C.func)
C.func = new_dec(C.func)
'''


def show_dir(func):
    for i in dir(func):
        if not hasattr(func, i):
            continue
        attr = getattr(func, i)
        print '{}.{}: '.format(func.__class__.__name__, i), attr
    return func


class caclculateTime(object):

    def __init__(self, is_debug):
        print 'Start {}'.format(self.__class__.__name__)
        # show_dir(self)
        self.is_debug = is_debug

    def __call__(self, func):
        def func_wrapper(*args, **kwargs):
            if self.is_debug is True:
                begin = time()
            ret = func(*args, **kwargs)
            if isinstance(ret, list):
                print 'List: {}'.format(str(ret))
            else:
                print 'Return value is not a list'
            if self.is_debug is True:
                logging.info(
                    '\n Function [{}] finished in {:.10f}s'.format(func.__name__, time() - begin))
            return ret
        return func_wrapper


def calculate_time(is_debug):
    def run_func(func):
        def func_wrapper(*args, **kwargs):
            if is_debug:
                begin = time()
                func(*args, **kwargs)
                logging.info(
                    "\n  Function [{}] finished in {:.10f}s".format(func.__name__, time() - begin))
            else:
                func(*args, **kwargs)
        return func_wrapper
    return run_func


def func(name):
    print "hello world, %s" % name
    for i in xrange(10000):
        i ** 3


@caclculateTime(True)
def test0():
    func('test0')
    return [1, 2, 3]


@caclculateTime(True)
def test1():
    func('test1')
    return {'ret': False}


@calculate_time(True)
def test2():
    func('test2')


@calculate_time(False)
def test3():
    func('test3')


class TDecorator(object):

    def dec(func):
        def func_wrapper(*args, **kwargs):
            print args
            print kwargs
            print url
            func(*args, **kwargs)
        return func_wrapper

    @dec
    def func(self, url):
        print 'URL: %s' % url


if __name__ == "__main__":
    test0()
    test2()
    print '----'
    test1()
    test3()
