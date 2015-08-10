# -*- coding: utf-8 -*-

from ConfigParser import (MAX_INTERPOLATION_DEPTH,
                          InterpolationDepthError,
                          InterpolationSyntaxError,
                          InterpolationMissingOptionError)
import ConfigParser
import re
import hashlib
import time
import logging
from requests.exceptions import InvalidURL
import requests
from lxml import etree

log = logging.getLogger(__name__)

BLOCK_SIZE = 1 << 15
server_regex = re.compile(
    r'^(?P<schema>https?://)?'  # http:// or https://
    # domain...
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    # r'(?:/?|[/?]\S+)  $ path and params
    r'$', re.IGNORECASE)


header_dict = {
    "0": "success",
    "1": "partial fail",
    "2": "fail"
}


def assert_header(header, status=0):
    '''
    { "header": {
        "status": 0,
        "desc": "success"
        }
    }
    '''
    assert header.status == status and header.desc == header_dict[
        str(status)], 'Header: %s' % header


def write_file(generator, filename, size=BLOCK_SIZE, mode='wb'):
    '''
    @param gemerator: generator to produce content
    @param filename: name of downloaded file
    @param size: block size
    @param mode: 'w', 'wb'
    '''
    with open(filename, mode) as f:
        for chunk in generator:
            if chunk:
                f.write(chunk)
    return filename


_encode_params = requests.PreparedRequest._encode_params


headers = {
    #'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    #'Accept-Encoding': 'gzip, deflate',
    #'Accept-Language': 'zh-CN,zh;q=0.8',
    #'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Length': '0',
    'Content-Type': 'application/x-www-form-urlencoded',
    # 'Cookie': r.headers.get('set-cookie'),
    #'Host': '',
    # 'Origin': 'http://',
    # 'Referer': 'http://',
    #'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36'
}


def prepare_cookies(session, server, username, password, headers=headers):
    '''
    @param session: session
    @param server: server address
    @param username: username
    @param password: password
    @return cookies of login account
    '''
    r = session.get(server)
    assert r.status_code == 200, 'Failed to get page "%s": %d Error' % (
        server, r.status_code)
    page = etree.HTML(r.content)
    payload = {}
    for e in page.xpath('//input'):
        payload[e.get('name')] = e.get('value')
    payload.update(
        username=username,  password=password,  captchaResponse='1')

    data = _encode_params(payload)
    res = session.post(
        r.url, headers=headers, verify=False, params=r.cookies, data=data)
    assert 'login' not in res.url.lower(), 'Login failed!'
    return session.cookies


def validate_url(value):
    match = server_regex.match(value)
    if match is None:
        raise InvalidURL
    if match.group('schema') is None:
        value = 'http://%s' % value
    return value


def timeout_alert(threshold):
    def run_func(func):
        def func_wrapper(*args, **kwargs):
            begin = time.time()
            ret = func(*args, **kwargs)
            spent = time.time() - begin
            if threshold > 0 and spent >= threshold:
                log.warning(
                    u"[{name}] 耗时: {time:.10f}s".format(
                        name=func.__name__, time=spent))
            else:
                log.info(
                    u"[{name}] 耗时: {time:.10f}s".format(
                        name=func.__name__, time=spent))
            return ret
        return func_wrapper
    return run_func


class AssertError(Exception):

    def __init__(self, key=None, msg=None):
        self.key = key
        self.msg = 'Assersion Error: %s' % msg


def md5_of_file(obj, block_size=BLOCK_SIZE, md5=None):
    '''
    @param filename: could be a file-like object or a file
    @param block_size: default to be 1<<15
    @param md5: the default md5 class

    Block size directly depends on the block size of your filesystem
    to avoid performances issues
    Here I have blocks of 2**15 octets (Default NTFS)
    '''
    md5 = md5 or hashlib.md5()

    def iter_read(obj, block_size):
        return iter(lambda: obj.read(block_size), '')

    func = lambda x: md5.update(x)
    if hasattr(obj, 'read'):
        map(func, iter_read(obj, block_size))
    else:
        with open(obj, 'rb') as fobj:
            map(func, iter_read(fobj, block_size))
    return md5


def sub_commas(s):
    '''
    reg = re.compile('[^",]*(?P<commas>,*)([^",]*)("[^"]*")*')
    '''
    ret = ''
    flag = 0b00
    for i in s:
        if i == ',' and 0 == flag & 0b01:
            if flag ^ 0b10:
                ret = ret + i
                flag = flag | 0b10
        else:
            if i == '"':
                flag = flag ^ 0b1
            ret = ret + i
            flag = flag & 0b01
    return ret


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


SEQUENCE_TYPE = (list, tuple, set)
MAPPING_TYPE = (dict,)
CONTAINER_TYPE = SEQUENCE_TYPE + MAPPING_TYPE


def assert_dict(D, expected_dict):
    """
    """
    '''
    print 'raw_dict: %s' % D
    print 'exp_dict: %s' % expected_dict
    print ''.ljust(65, '-')
    '''
    if isinstance(D, MAPPING_TYPE) is False:
        return False
    for k in expected_dict.iterkeys():
        if k not in D:
            return AssertError(key=k, msg='%s missing' % k)
        ret = assert_object(D.get(k), expected_dict.get(k))
        if ret is not True:
            return ret
    return True


def assert_list(L, expected_list):
    if isinstance(L, SEQUENCE_TYPE) is False:
        return False
    for i in expected_list:
        # 可能是乱序的……
        for j in L:
            ret = assert_object(j, i)
            if ret is True:
                break
        else:
            return ret
    return True


def assert_object(obj, expected_obj, allow_fuzzy=True):
    """
    :param ojbect: should be python object
    :param expected_obj: should be python object
    :return boolean or Exception
    """
    log.info('raw: %s' % obj)
    log.info('exp: %s' % expected_obj)
    log.info(''.ljust(65, '*'))
    if expected_obj in [None, '*']:
        return True
    if isinstance(expected_obj, CONTAINER_TYPE) is False:
        return obj == expected_obj
    # Deal with (list, tuple, dict)
    # dict
    if isinstance(expected_obj, MAPPING_TYPE):
        return assert_dict(obj, expected_obj)
    # list, tuple
    if isinstance(expected_obj, SEQUENCE_TYPE):
        return assert_list(obj, expected_obj)


def yield_infinite(gen):  # infinitely
    g = gen()
    while True:
        try:
            flag = yield g.next()
            if flag is False:
                raise StopIteration
        except StopIteration:
            if flag is not False:
                g = gen()
            else:
                raise


class SafeConfigParser(ConfigParser.SafeConfigParser):
    _interpvar_re = re.compile(r"%\(([^)]+)\)")

    def _interpolate(self, section, option, rawval, vars):
        # do the string interpolation
        if isinstance(rawval, basestring) is False:
            return rawval
        L = []
        self._interpolate_some(option, L, rawval, section, vars, 1)
        return L[0] if len(L) == 1 else ''.join(str(i) for i in L)

    def _interpolate_some(self, option, accum, rest, section, map, depth):
        if depth > MAX_INTERPOLATION_DEPTH:
            raise InterpolationDepthError(option, section, rest)
        while rest:
            p = rest.find("%")
            if p < 0:
                accum.append(rest)
                return
            if p > 0:
                accum.append(rest[:p])
                rest = rest[p:]
            # p is no longer used
            c = rest[1:2]
            if c == "%":
                accum.append("%")
                rest = rest[2:]
            elif c == "(":
                m = self._interpvar_re.match(rest)
                if m is None:
                    raise InterpolationSyntaxError(option, section,
                                                   "bad interpolation variable reference %r" % rest)
                # case sensitive
                # var = self.optionxform(m.group(1))
                var = m.group(1)
                rest = rest[m.end():]
                try:
                    # Cross Section
                    # v = map[var]
                    var_list = var.split('.')
                    if len(var_list) == 1:
                        v = map[var]
                    else:
                        v = self._sections.get(var_list[0]).get(var_list[1])
                        for attr in var_list[2:]:
                            v = v.get(attr)
                except KeyError:
                    raise InterpolationMissingOptionError(
                        option, section, rest, var)
                if isinstance(v, basestring) and "%" in v:
                    self._interpolate_some(option, accum, v,
                                           section, map, depth + 1)
                else:
                    accum.append(v)
            else:
                raise InterpolationSyntaxError(
                    option, section,
                    "'%%' must be followed by '%%' or '(', found: %r" % (rest,))
