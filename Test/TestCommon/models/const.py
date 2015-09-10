#! -*- coding:utf8 -*-

'''
store `const` in common
'''
import logging
import sys

__all__ = ('STDOUT', 'BLANK', 'API_STATUS', 'WIDTH')

STDOUT = logging.StreamHandler(sys.stdout)
STDOUT.setLevel(logging.DEBUG)


class ConstType(type):

    '''
    def __new__(cls, name, bases, attrs):

        if name == 'None':
            return None

        # Go over attributes and see if they should be renamed.
        newattrs = {}
        for attrname, attrvalue in attrs.iteritems():
            if attrname.startswith('_'):
                newattrs[attrname] = attrvalue

        newattrs['__dict__'] = {}
        for attrname, attrvalue in attrs.iteritems():
            if not attrname.startswith('_'):
                newattrs['__dict__'][attrname] = attrvalue

        return super(ConstType, cls).__new__(cls, name, bases, newattrs)
    '''
    def __repr__(cls):
        newdict = dict((k, v)
                       for k, v in cls.__dict__.items() if not k.startswith('_'))
        return '<const {}>{}'.format(cls.__name__, newdict if newdict else '')


class ConstObject(object):
    __metaclass__ = ConstType


class BLANK(ConstObject):

    '''
    改变字典的值，有3个概念：
    1. 不改变，意即不对该键值做任何改动
    2. 删除，意即 BLANK 的含义
    3. 为空，意即 None
    '''
    pass


class API_STATUS(ConstObject):

    '''
    这是 API 传回的 STATUS 枚举表
    '''
    SUCCESS = 'PASS'
    FAILED = 'FAIL'
    EXCEPTION = 'ERROR'


class WIDTH(ConstObject):
    DESCRIPTION = 72
    STATUS = 5
    RUNTIME = 6


class CPC_LEVEL(ConstObject):
    pass

MIME_TYPES = {
    '.csv': 'text/csv',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xltx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
    '.potx': 'application/vnd.openxmlformats-officedocument.presentationml.template',
    '.ppsx': 'application/vnd.openxmlformats-officedocument.presentationml.slideshow',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.sldx': 'application/vnd.openxmlformats-officedocument.presentationml.slide',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.dotx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.template',
    '.xlsm': 'application/vnd.ms-excel.addin.macroEnabled.12',
    '.xlsb': 'application/vnd.ms-excel.sheet.binary.macroEnabled.12',
}
