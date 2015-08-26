#! -*- coding:utf8 -*-


def len_unicode(s, encoding='utf8'):
    '''
    unicode lenght in python is 3-bytes
    convert it into 2-bytes

    >>> len(u'哈哈')
    6
    >>> len_unicode(u'哈哈')
    4
    >>> len(u'哈哈a')
    7
    >>> len_unicode(u'哈哈a')
    5
    '''
    if isinstance(s, str):
        return (len(s) + len(s.decode(encoding))) / 2
    return (len(s.encode(encoding)) + len(s)) / 2


from .models.common import TestResult
from .models.const import STATUS
from .exceptions import UndefinedException
from time import clock
from . import ThreadLocal
import random
import string
import collections


def secondsToStr(t):
    return "%d:%02d:%02d.%03d" % \
        reduce(lambda ll, b: divmod(ll[0], b) + ll[1:],
               [(t * 1000,), 1000, 60, 60])


def formatter(func):
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
                tr.message = '[%s] %s' % (type(e).__name__, e.message)
            else:
                tr.message = '[%s] %s' % (type(e).__name__,  ','.join(e.args))
        tr.function = '%s.%s' % (func.__module__, func.__name__)
        tr.runtime = clock() - begin
        ThreadLocal.get_results().append(tr)
        return tr
    return wrapper


def mount(obj):
    def decorator(func):
        obj.__dict__[func.__name__] = func

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator

results = ThreadLocal.get_results()


def suite(labels):
    if not isinstance(labels, collections.MutableSequence):
        labels = [labels]

    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        for label in labels:
            ThreadLocal.get_suites()[label].add(wrapper)
        return wrapper
    return decorator


def _gen_random_chinese():
    '''
    @return a unicode: A Chinese

    GBK: 0x8140~0xfefe
    s = '%x%x' % (random.randint(0x81, 0xFE), random.randint(0x40, 0xFE))

    GB2312
    '''
    s = '%x%x' % (random.randint(0xB0, 0xF7), random.randint(0xA1, 0xFE))
    try:
        return s.decode('hex').decode('gbk')
    except UnicodeDecodeError:
        return _gen_random_chinese()


def gen_chinese_unicode(length, unicode_encoded=True):
    '''
    @param length: target length of unicode
    @return a `str` string
    BTW: A Chinese has length of `2`
    '''
    s = ''
    _length = length
    while length > 1:
        if random.choice([True, False]):
            s += _gen_random_chinese()
            length = length - 2
        else:
            # Let ascii be induplicate
            # s += gen_random_ascii(1)
            length = length - 1
    s += gen_random_ascii(_length - len(s) * 2)
    s = ''.join(random.sample(s, len(s)))
    if unicode_encoded:
        return s
    return s.encode('utf8')


def gen_random_ascii(length, unicode_encoded=True):
    '''
    @return unicode if `unicode_encoded == True` else string
    '''
    if length < 1:
        return ''
    s = ''.join(random.sample(string.ascii_letters + string.digits, length))
    if unicode_encoded:
        s = s.decode('utf8')
    return s
