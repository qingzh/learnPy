#! -*- coding:utf8 -*-

from .models.common import TestResult
from .models.const import STATUS
from .exceptions import UndefinedException
from time import clock
import collections
from functools import wraps
from . import ThreadLocal


def secondsToStr(t):
    return "%d:%02d:%02d.%03d" % \
        reduce(lambda ll, b: divmod(ll[0], b) + ll[1:],
               [(t * 1000,), 1000, 60, 60])

ErrorFormat = '[{}] {}'
NameFormat = '{}.{}'


def formatter(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        tr = TestResult(description=func.func_doc)
        begin = clock()
        try:
            func(*args, **kwargs)
            tr.status = STATUS.SUCCESS
            tr.message = STATUS.SUCCESS
        except AssertionError as e:
            tr.status = STATUS.FAILED
            tr.message = e.message
        except UndefinedException as e:
            tr.status = None
            tr.message = e.message
        except Exception as e:
            tr.status = STATUS.EXCEPTION
            if e.message:
                tr.message = ErrorFormat.format(type(e).__name__, e.message)
            else:
                tr.message = ErrorFormat.format(
                    type(e).__name__,  ','.join(e.args))
        tr.function = NameFormat.format(func.__module__, func.__name__)
        tr.runtime = clock() - begin
        ThreadLocal.get_results().append(tr)
        return tr
    return wrapper


def mount(obj):
    '''
    最后回传的是wrapper
    '''
    def decorator(func):
        obj.__dict__[func.__name__] = func

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator

results = ThreadLocal.get_results()


def suite(labels):
    if not isinstance(labels, collections.MutableSequence):
        labels = [labels]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        suites = ThreadLocal.get_suites()
        suites['ALL'].add(wrapper)
        for label in labels:
            suites[label].add(wrapper)
        return wrapper
    return decorator
