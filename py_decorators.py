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
from time import clock
from functools import update_wrapper

log = logging.getLogger()
log.setLevel(logging.DEBUG)


class C(object):

    def func(self, n):
        ''' Original DOC in C.func '''
        log.debug('%s.%s: %s' % (self.__class__, func.__name__, n))
        log.debug(func.__doc__)
        return n * 2


def dec(func):
    def wrapper(*args, **kwargs):
        ''' It's a NEW doc '''
        log.debug(wrapper.__doc__)
        return func(*args, **kwargs)
    return update_wrapper(wrapper, func)


def new_dec(func):
    def wrapper(*args, **kwargs):
        ''' Another NEW doc '''
        log.debug(wrapper.__doc__)
        return func(*args, **kwargs) * 5
    return update_wrapper(wrapper, func)

'''
C.new_func = dec(C.func)
C.func = new_dec(C.func)
'''


class caclculateTime(object):

    def __init__(self, is_debug):
        log.info('Start {}'.format(self.__class__.__name__))
        self.is_debug = is_debug

    def __call__(self, func):
        def func_wrapper(*args, **kwargs):
            '''
            Doc in func_wrapper
            '''
            if self.is_debug is True:
                begin = clock()
            ret = func(*args, **kwargs)
            if isinstance(ret, list):
                print 'List: {}'.format(str(ret))
            else:
                print 'Return value is not a list'
            if self.is_debug is True:
                log.info(
                    '\n Function [{}] finished in {:.10f}s'.format(func.__name__, clock() - begin))
            return ret
        return func_wrapper


def calculate_time(is_debug):
    def run_func(func):
        def func_wrapper(*args, **kwargs):
            if is_debug:
                begin = clock()
                func(*args, **kwargs)
                log.info(
                    "\n  Function [{}] finished in {:<.10f}s".format(func.__name__, clock() - begin))
            else:
                func(*args, **kwargs)
        return update_wrapper(func_wrapper)
    # also a decorator, no need to `update_wrapper`
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
