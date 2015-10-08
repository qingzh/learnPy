#! -*- coding:utf8 -*-

from .models.common import TestResult
from .models.const import STATUS
from .exceptions import UndefinedException
from time import clock
from functools import update_wrapper, partial
from .threadlocal import ThreadLocal
from .utils import is_sequence
import inspect
import os.path
import traceback

__all__ = ['formatter', 'mount', 'suite']
FORMATTER_SWITCH = True


def secondsToStr(t):
    return "%d:%02d:%02d.%03d" % \
        reduce(lambda ll, b: divmod(ll[0], b) + ll[1:],
               [(t * 1000,), 1000, 60, 60])

ErrorFormat = '[{}] {}'


def formatter(func):
    if FORMATTER_SWITCH is False:
        return func

    def wrapper(*args, **kwargs):
        tr = TestResult(description=func.func_doc.strip())
        ret, begin = None, clock()
        try:
            ret = func(*args, **kwargs)
            tr.status = STATUS.SUCCESS
            message = 'SUCCESS'
        except AssertionError as e:
            tr.status = STATUS.FAILURE
            message = e.message
        except UndefinedException as e:
            tr.status = STATUS.UNDEFINED
            message = e.message
        except Exception as e:
            tr.status = STATUS.EXCEPTION
            message = traceback.format_exc()
        tr.message = message.decode('unicode_escape')
        tr.runtime = clock() - begin
        tr.function = func.__name__
        mname = func.__module__
        if mname == '__main__':
            mname = os.path.basename(inspect.getfile(func))
        tr.module = mname
        ThreadLocal.get_results().append(tr)
        return ret
    return update_wrapper(wrapper, func)


def mount(obj, *args, **kwargs):
    '''
    最后回传的是wrapper
    '''
    def decorator(func):
        obj.__dict__[func.__name__] = partial(func, *args, **kwargs)
        return func
    return decorator


class suite(object):

    def __init__(self, labels):
        self.labels = is_sequence(labels, convert=True)

    def __call__(self, func):
        suites = ThreadLocal.suites
        suites['ALL'].add(func)
        for label in self.labels:
            suites[label].add(func)
        return func
