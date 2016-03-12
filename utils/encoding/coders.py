#! -*- coding:utf8 -*-
"""
* encode(): Gets you from Unicode -> bytes
* decode(): Gets you from bytes -> Unicode
* codecs.open(encoding="utf8"): Read and write files directly to/from Unicode (you can use any encoding, not just utf8, but utf8 is most common).

$ cat temp.log
中文ABC
$ ipython

>>> import codecs
>>> with open('temp.log', 'r') as f: s1 = f.read()
>>> with codecs.open('temp.log', 'r', encoding='utf8')as f: s2 = f.read()
>>> type(s1)
<type 'str'>

>>> type(s2)
<type 'unicode'>

* u"": Makes your string literals into Unicode objects rather than byte sequences.

"""
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
