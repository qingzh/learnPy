#! -*- coding:utf8 -*-

'''
store `const` in common
'''
import logging
import sys

STDOUT = logging.StreamHandler(sys.stdout)


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
    pass


class STATUS(ConstObject):
    SUCCESS = 'PASS'
    FAILED = 'FAIL'
    EXCEPTION = 'ERROR'


class SUITE(ConstObject):
    __metaclass__ = ConstType
    API = 0


class WIDTH(ConstObject):
    DESCRIPTION = 76
    STATUS = 5
    RUNTIME = 6
