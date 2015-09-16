#! -*- coding:utf8 -*-

# print '---- utils init ----'

import random
import string
import collections
import urlparse

__all__ = [
    '_compare_dict', 'prepare_url', 'is_sequence', 'len_unicode',
    'gen_chinese_unicode', 'gen_random_ascii', 'gen_files']


def _compare_dict(a, b):
    for key, value in a.iteritems():
        if value is None:
            continue
        assert value == b[key], 'Content Differ at key `%s`!\nExpected: %s\nActually: %s\n' % (
            key, value, b[key])


def prepare_url(server):
    '''
    namedtuple('ParseResult', 'scheme netloc path params query fragment')
    '''
    parsed = list(urlparse.urlparse(server))
    parsed[0] = parsed[0] or 'http'
    if not parsed[1]:
        parsed[1] = parsed[2]
        parsed[2] = ''
    return urlparse.urlunparse(parsed)


def is_sequence(val, convert=False):
    # 字符串类型需要单独判断
    if isinstance(val, basestring):
        return False if not convert else [val]
    # 同时也能判断自定义的  Sequence Type
    boo = isinstance(val, collections.Sequence)
    if not convert:
        return boo
    if boo:
        return val
    # iterable, like `dict`, `set`, `generator` ...
    if isinstance(val, collections.Iterable):
        return list(val)
    # not iterable, like `int`, `float`
    return [val] if val else list()


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

import os.path
from .models.const import MIME_TYPES
from requests.utils import quote


def gen_files(filename, filetype=None):
    '''
    generate `file` from filename to HTTP body(multipart/form-data)

    Sample usage:
    >>> requests.post(url, files=gen_file(filename, filetype))

    '''
    basename = os.path.basename(filename)
    if isinstance(basename, unicode):
        basename = basename.encode('utf-8')
    # 这里使用中文会有点问题……
    basename = quote(basename)
    if filetype is None:
        filetype = MIME_TYPES[os.path.splitext(basename)[1]]
    files = {
        'file': (basename, open(filename, 'rb'), filetype),
        'utilType': (None, 'WuliaoFile'),
        'fileName': (None, '')
    }
    return files
