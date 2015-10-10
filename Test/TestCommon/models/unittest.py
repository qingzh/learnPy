#! -*- coding:utf8 -*-

import logging
from ..decorators import formatter
from functools import update_wrapper

__all__ = ['TestCase',
]


class TestCase(object):

    @classmethod
    def decorator(cls, func):
        obj = func.im_self

        def wrapper(*args, **kwargs):
            obj.setUp()
            func(*args, **kwargs)
            obj.tearDown()
        return formatter(update_wrapper(wrapper, func))

    def __init__(self):
        self._testcases = []
        for name in dir(self):
            if name.startswith('test_') is False:
                continue
            method = getattr(self, name, None)
            if method is None:
                continue
            setattr(self, name, TestCase.decorator(method))
            self._testcases.append(name)

    def run(self):
        for name in self._testcases:
            method = getattr(self, name, None)
            if method is None:
                continue
            method()
