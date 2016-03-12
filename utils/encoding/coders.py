#! -*- coding:utf8 -*-

__all__ = ['encoder', 'decoder']


def decoder(s, encoding='utf8'):
    ''' string -> unicode '''
    # > A = u'中文ABC'  # unicode
    # u'\u4e2d\u6587ABC'
    # > B = u'中文ABC'.decode('unicode-escape')  # unicode
    # u'\xe4\xb8\xad\xe6\x96\x87ABC'
    # > C = '中文ABC'  # str
    # '\xe4\xb8\xad\xe6\x96\x87ABC'
    # > D = '中文ABC'.encode('unicode-escape')  # str
    # '\\u4e2d\\u6587ABC'
    """
    A: '\\u4e2d\\u6587ABC'
    B: '\xe4\xb8\xad\xe6\x96\x87ABC'
    C: '\\u4e2d\\u6587ABC'
    D: '\\u4e2d\\u6587ABC'
    """ 
    s = s.encode('unicode-escape').decode('string-escape')
    try:
        s.encode('ascii')
        return s.decode('unicode-escape')
    except UnicodeDecodeError:
        return unicode(s, encoding)


def encoder(s):
    ''' unicode -> string '''
    """
    A: '\\u4e2d\\u6587ABC'
    B: '\xe4\xb8\xad\xe6\x96\x87ABC'
    C: '\\u4e2d\\u6587ABC'
    D: '\\u4e2d\\u6587ABC'
    """ 
    s = s.encode('unicode-escape').decode('string-escape')
    try:
        s.encode('ascii')
        return s.decode('unicode-escape').encode('utf8')
    except UnicodeDecodeError:
        return s
