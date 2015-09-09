#! -*- coding:utf8 -*-

from .models.common import TestResult
from .models.const import API_STATUS
from .exceptions import UndefinedException
from time import clock
from functools import update_wrapper
from . import ThreadLocal
from .utils import is_sequence

__all__ = ['formatter', 'mount', 'suite']


def secondsToStr(t):
    return "%d:%02d:%02d.%03d" % \
        reduce(lambda ll, b: divmod(ll[0], b) + ll[1:],
               [(t * 1000,), 1000, 60, 60])

ErrorFormat = '[{}] {}'
NameFormat = '{}.{}'


def formatter(func):
    def wrapper(*args, **kwargs):
        tr = TestResult(description=func.func_doc)
        begin = clock()
        try:
            func(*args, **kwargs)
            tr.status = API_STATUS.SUCCESS
            tr.message = API_STATUS.SUCCESS
        except AssertionError as e:
            tr.status = API_STATUS.FAILED
            tr.message = e.message
        except UndefinedException as e:
            tr.status = None
            tr.message = e.message
        except Exception as e:
            tr.status = API_STATUS.EXCEPTION
            if e.message:
                tr.message = ErrorFormat.format(type(e).__name__, e.message)
            else:
                tr.message = ErrorFormat.format(
                    type(e).__name__,  ','.join(e.args))
        tr.function = NameFormat.format(func.__module__, func.__name__)
        tr.runtime = clock() - begin
        ThreadLocal.get_results().append(tr)
        return tr
    return update_wrapper(wrapper, func)


def mount(obj):
    '''
    最后回传的是wrapper
    '''
    def decorator(func):
        obj.__dict__[func.__name__] = func
        return func
    return decorator


class suite(object):

    def __init__(self, labels):
        self.labels = is_sequence(labels, convert=True)

    def __call__(self, func):
        suites = ThreadLocal.get_suites()
        suites['ALL'].add(func)
        for label in self.labels:
            suites[label].add(func)
        return func
