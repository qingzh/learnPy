#! -*- coding:utf8 -*-
'''

只要这个文件被调用过，例如
from xxx import compat
那么 调用之后的所有的 requests 都会变成自定义的requests
因为不管从何处引入，只要不改变 requests 本身，则requests 对象地址不变！

'''
# print '---- compat init ----'

import requests
from functools import update_wrapper
from .models.const import LOG_LEVEL
import logging

__all__ = []

requests.__doc__ = "TestCommon requests"
'''
# partial 应用在类方法上有些问题
# 会出现异常：
#   unbound method send() must be called with Session instance as first argument (got PreparedRequest instance instead)
# 例如：
"""
from functools import partial
class C(object):
    def func(self, a, **kwargs):
        return a+kwargs['c']
    def ff(self, c=0):
        return self.func(7, c=c)
>>> C.func = partial(C.func, c=20)
>>> c = C()
>>> c.ff()
TypeError: unbound method func() must be called with C instance as first argument (got int instance instead)
"""


_original_send = requests.Session.send
requests.Session.send = partial(_original_send, verify=False)
'''


def send_dec(func):
    def wrapper(self, *args, **kwargs):
        kwargs['verify'] = False
        return func(self, *args, **kwargs)
    return update_wrapper(wrapper, func)

_original_send = requests.Session.send
requests.Session.send = send_dec(_original_send)

'''
设置 logging 默认等级的方法
1. 修改 Logger.__init__
2. 修改 getLogger
'''


def logger_dec(func):
    def wrapper(name=None):
        logger = func(name)
        logger.setLevel(LOG_LEVEL)
        return logger
    return update_wrapper(wrapper, func)

logging.getLogger = logger_dec(logging.getLogger)
