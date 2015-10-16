#! -*- coding:utf8 -*-


import json
import logging
from ..utils import len_unicode, is_sequence
from .const import *
from ..exceptions import ReadOnlyAttributeError

__all__ = [
    'AttributeDict', 'APIAttributeDict', 
    'ReadOnlyObject', 'PersistentAttributeObject',
    'TestResult', 'SlotsDict', 'AttributeDictWithProperty',
]

log = logging.getLogger(__name__)


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
        for key in self.keys():
            # Nested AttributeDict object
            # new object should be instance of self.__class__
            # compatible with `property`
            value = self[key]
            AttributeDict.__setitem__(self, key, value)

    def __hash__(self):
        return hash(self.__str__())

    @property
    def __classhook__(self):
        return self.__class__

    def __getitem__(self, key):
        # `dict` item first
        # 这里允许通过[key] 形式来获取属性
        # 但是如果设置有 Property 那么就不能这么做
        if key in self:
            return super(AttributeDict, self).__getitem__(key)
        return super(AttributeDict, self).__getattribute__(key)

    '''
    # __getattr__ 方法实际上不用实现
    # 在获取属性的时候，会默认从 self.__class__的属性 以及 self.__dict__ 里获取
    # 如果获取失败，才从 __getattr__ 获取
    def __getattr__(self, key):
        # Attribute First
        # 这里不能用 `dir(self)`，会进入死循环，参考dir的实现逻辑
        print '__getattr__', key
        if key in dir(self.__class__) or key in self.__dict__:
            return super(AttributeDict, self).__getattribute__(key)
        return super(AttributeDict, self).__getitem__(key)
    '''

    __getattr__ = dict.__getitem__

    def _is_parent_instance(self, value):
        '''
        return issubclass(self.__classhook__, type(value)) and \
            not isinstance(value, self.__classhook__)
        '''
        return type(value) in self.__classhook__.__mro__[1:]

    def __setitem__(self, key, value):
        # Nested AttributeDict object
        log.debug('Obj: %s\nkey: %s, value: %s', type(self), key, value)
        # sequence
        if is_sequence(value):
            for idx, item in enumerate(value):
                if self._is_parent_instance(item):
                    value[idx] = self.__classhook__(item)
        elif self._is_parent_instance(value):
            value = self.__classhook__(value)
        super(AttributeDict, self).__setitem__(key, value)

    def __setattr__(self, key, value):
        """
        不允许通过 __setattr__ 新增对象属性
        但是允许通过 __setattr__ 修改对象已有的属性
        如果需要新增属性，则需要修改 self.__dict__
        例如：iterkeys, __dict__ 之类
        """
        if key in dir(self.__class__) or key in self.__dict__:
            super(AttributeDict, self).__setattr__(key, value)
        else:
            self.__setitem__(key, value)

    def __call__(self, *args, **kwargs):
        '''

        self.update(...)
        '''
        super(AttributeDict, self).update(*args, **kwargs)
        return self

    def __str__(self):
        return json.dumps(self)

    def json(self, allow_null=None, filter=None):
        return json.dumps(self)

    def copy(self):
        return type(self)(self)

    def update(self, *args, **kwargs):
        d = dict(*args, **kwargs)
        for key in d.iterkeys():
            self.__setitem__(key, d[key])


class AttributeDictWithProperty(AttributeDict):

    '''
    允许设置字典的property
    property属性通过 __setattribute__ 调用
    property方法里调用 同样名称的元素 (__item__)
    '''
    """ FIXME
    还要定制 __getitem__ __getattr__
    """

    def __init__(self, *args, **kwargs):
        """
        take care of nested dict
        """
        super(AttributeDict, self).__init__(*args, **kwargs)
        for key in self.keys():
            # Nested AttributeDict object
            # new object should be instance of self.__class__

            # compatible with `property`
            value = self[key]
            if isinstance(getattr(self.__class__, key, None), property):
                getattr(self.__class__, key).__set__(self, value)
            else:
                AttributeDictWithProperty.__setitem__(self, key, value)

    __getitem__ = dict.__getitem__
    
    def __setitem__(self, key, value):
        if value == BLANK:
            # clear item
            return self.pop(key, BLANK)
        super(AttributeDictWithProperty, self).__setitem__(key, value)


class APIAttributeDict(AttributeDict):

    @property
    def nodes(self):
        '''
        get all url paths
        '''
        path = {}
        for k, v in self.iteritems():
            if isinstance(v, APIAttributeDict):
                path.update(v.nodes)
            else:
                path[k] = v
        return path


class ReadOnlyObject(object):

    def __setitem__(self, key, value):
        raise ReadOnlyAttributeError(
            "%s.%s is read-only!" % (self.__class__, key))

    def __setattr__(self, key, value):
        if key in dir(self.__class__):
            super(ReadOnlyObject, self).__setattr__(key, value)
        else:
            raise ReadOnlyAttributeError(
                "%s.%s is read-only!" % (self.__class__, key))


class PersistentAttributeObject(object):

    '''
    __slots__ 是限制类属性 .__dict__
    那么，怎么限制 元素 呢？
    '''

    def __setitem__(self, key, value):
        if getattr(self, key, BLANK) is BLANK:
            raise KeyError(
                "%s.%s is not exist!" % (self.__class__, key))
        super(PersistentAttributeObject, self).__setitem__(key, value)

    def __setattr__(self, key, value):
        if key in dir(self.__class__):
            super(PersistentAttributeObject, self).__setattr__(key, value)
        else:
            PersistentAttributeDict.__setitem__(self, key, value)

    def update(self, *args, **kwargs):
        _dict = dict(*args, **kwargs)
        if set(_dict).issubset(self) is False:
            raise KeyError("Can NOT add keys: %s!" %
                           (set(_dict).difference(self)))
        for key, value in _dict.iteritems():
            # super(PersistentAttributeObject, self).__setitem__(key, value)
            self.__setitem__(key, value)

    def update_existed(self, *args, **kwargs):
        _dict = dict(*args, **kwargs)
        for key, value in _dict.iteritems():
            if key in self:
                self.__setitem__(key, value)


class SlotsDict(PersistentAttributeObject, AttributeDict):
    __classhook__ = AttributeDict

    def __init__(self, *args, **kwargs):
        # TODO: not compatible with nested dict
        _dict = {}
        for key in self.__slots__:
            _dict[key] = getattr(self.__class__, key, None)
        super(SlotsDict, self).__init__(_dict)
        super(SlotsDict, self).update(*args, **kwargs)

    def __setitem__(self, key, value):
        if key not in self.__slots__:
            raise KeyError(
                "%s.%s is not exist!" % (self.__class__, key))
        super(SlotsDict, self).__setitem__(key, value)
        super(SlotsDict, self).__setattr__(key, value)

    __setattr__ = __setitem__


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
    return ('{:>%d.2f}' % width).format(f)

STATUS_MAP = {
    STATUS.SUCCESS: 'PASS',
    STATUS.FAILURE: 'FAIL',
    STATUS.EXCEPTION: 'ERROR',
    STATUS.UNDEFINED: 'UNDEF'
}


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
        self.module = None
        super(TestResult, self).__init__(*args, **kwargs)

    def pretty(self, encoding='utf8'):
        '''
        | %80s | PASS |
        | %76s | FAIL |
        '''
        pretty = []
        lines = [x.strip()
                 for x in (self.description or '').strip().split('\n')
                 if x.strip()] or ['']
        pretty.append(
            ' | '.join([
                _pretty_description(lines[0]),
                _pretty_status(STATUS_MAP[self.status]),
                _pretty_runtime(self.runtime)
            ]))
        for i in range(1, len(lines)):
            pretty.append(
                ' | '.join([
                    _pretty_description(lines[i]),
                    _pretty_status(''),
                    _pretty_string('', WIDTH.RUNTIME)
                ]))
        return '\n'.join(pretty)
