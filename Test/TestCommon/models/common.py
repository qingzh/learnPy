#! -*- coding:utf8 -*-

import json
from ..utils import len_unicode
from .const import *

__all__ = ['AttributeDict', 'TestResult']


class AttributeDict(dict):

    '''
    怎么剥离出 property
    定义了 property 但是会跳到dict内容
    只能把 dict 剥离出来当成一个内部变量？
    '''

    def __init__(self, *args, **kwargs):
        """
        take care of nested dict
        """
        super(AttributeDict, self).__init__(*args, **kwargs)
        for key, value in self.iteritems():
            # Nested AttributeDict object
            # new object should be instance of self.__class__
            AttributeDict.__setitem__(self, key, value)

    __getattr__ = dict.__getitem__

    def __setitem__(self, key, value):
        # Nested AttributeDict object
        if isinstance(value, dict) and not isinstance(value, self.__class__) and issubclass(self.__class__, type(value)):
            value = self.__class__(value)
        super(AttributeDict, self).__setitem__(key, value)

    def __setattr__(self, key, value):
        """
        字典里不允许存在类默认的属性
        例如：iterkeys, __dict__ 之类
        """
        if key in dir(self.__class__):
            super(AttributeDict, self).__setattr__(key, value)
        else:
            self.__setitem__(key, value)

    def __str__(self):
        return json.dumps(self)

    def json(self, allow_null=None, filter=None):
        return json.dumps(self)

    def copy(self):
        return type(self)(self)


def _pretty_description(s, width=WIDTH.DESCRIPTION, encoding='utf8'):
    ''' width: 76 '''
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return s.rjust(width + len(s) - len_unicode(s))


def _pretty_status(s, width=WIDTH.STATUS):
    if s is None:
        s = '-'
    return s.rjust(width)


def _pretty_string(s, width):
    if s is None:
        s = '-'
    return s.rjust(width)


def _pretty_runtime(f, width=WIDTH.RUNTIME):
    if f is None:
        return '-'.rjust(width)
    f = float(f)
    return ('{:%d.2f}' % width).format(f)


class TestResult(AttributeDict):

    '''
    我们需要定义一个测试结果记录的接口
    1. 便于格式化结果记录
    2. 便于和其他系统交互
    3. 使用Json格式 ~ 通用

    接口定义如下：
    Status: enum  # 运行结果(结果正常，结果错误，运行异常)
    Message: string      # 错误信息/异常信息
    Description: string  # 测试描述, PEP8标准下不超过76个字符(至少4个缩进)
    Name: string # 测试名，默认是函数名？
    Suite: string[] # 所属测试集: Sales, API, CPC
    Label: string[] # 测试分级，smoke?integration?
    id: int # 编号，保留属性
    Runtime: float  # 运行时间

    以上key均为小写
    其实 Suite 和 Label 可以合并？
    问题1：在A测试集是smoke case 另一个测试集是否也是smoke case？

    '''

    def __init__(self, *args, **kwargs):
        self.status = None
        self.message = None
        self.description = None
        self.name = None
        self.suite = None
        self.id = None
        self.runtime = None  # seconds
        self.function = None
        super(TestResult, self).__init__(*args, **kwargs)

    def pretty(self, encoding='utf8'):
        '''
        | %80s | PASS |
        | %76s | FAIL |
        '''
        pretty = []
        lines = [x.strip()
                 for x in (self.description or '').strip().split('\n') if x.strip()] or ['']
        pretty.append(
            ' | '.join([_pretty_description(lines[0]), _pretty_status(self.status), _pretty_runtime(self.runtime)]))
        for i in range(1, len(lines)):
            pretty.append(
                ' | '.join([_pretty_description(lines[i]), _pretty_status(''), _pretty_string('', WIDTH.RUNTIME)]))
        return '\n'.join(pretty)
