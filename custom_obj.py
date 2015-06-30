# -*- coding: utf-8 -*-

"""

"""

import json


class JSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, 'dict'):
            return obj.dict()
        super(JSONEncoder, self).default(obj)


class ReadOnlyAttributeError(Exception):
    pass


class ReadOnlyObject(object):

    def __setitem__(self, key, value):
        raise ReadOnlyAttributeError(
            "%s.%s is read-only!" % (self.__class__, key))
    __setattr__ = __setitem__


class ReadOnlyAttributeDict(ReadOnlyObject, dict):

    def __init__(self, *args, **kwargs):
        """
        take care of nested dict
        """
        dict.__init__(self, *args, **kwargs)
        object.__setattr__(self, '__dict__', self)
        for key, value in self.iteritems():
            if isinstance(value, dict) and not isinstance(value, ReadOnlyAttributeDict):
                dict.__setitem__(self,
                                 key, ReadOnlyAttributeDict(value))


class AttributeDict(dict):

    '''
    we expect nested AttributeDict to be ReadOnlyAttributeDict ...
    attr_dict = {
                  "a": 1,
                  "b": {
                    "c": 3,
                    "d": {
                      "e": 5
                    }
                  },
                  "f": None
                }

    >>> d = AttributeDict(attr_dict)
    >>> d.keys = 123
    ReadOnlyAttributeError                    Traceback (most recent call last)
    ...
    >>> d.f.g = 7
    AttributeError: 'NoneType' object has no attribute 'g'
    >>> d.a = {}
    >>> d.g = 7
    >>> d
    {'a': {}, 'b': {'c': 3, 'd': {'e': 5}}, 'f': None, 'g': 7}

    '''

    def __init__(self, *args, **kwargs):
        """
        take care of nested dict
        """
        super(AttributeDict, self).__init__(*args, **kwargs)
        # self.__dict__ = self
        for key, value in self.iteritems():
            # nested object
            if isinstance(value, dict) and not isinstance(value, AttributeDict):
                # get rid of override '__setattr__'
                super(AttributeDict, self).__setattr__(
                    key, AttributeDict(value))

    __getattr__ = dict.__getitem__

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, self.__class__):
            value = AttributeDict(value)
        super(self.__class__, self).__setitem__(key, value)

    def __setattr__(self, key, value):
        """
        字典里不允许存在类默认的属性
        例如：iterkeys, __dict__ 之类
        """
        if key in dir(AttributeDict):
            super(AttributeDict, self).__setattr__(key, value)
        else:
            self.__setitem__(key, value)


class ReadOnlyAttributeDict(ReadOnlyObject, AttributeDict):

    '''
    we expect nested AttributeDict to be ReadOnlyAttributeDict ...
    attr_dict = {
                  "a": 1,
                  "b": {
                    "c": 3,
                    "d": {
                      "e": 5
                    }
                  },
                  "f": None
                }

    >>> d = ReadOnlyAttributeDict(attr_dict)
    >>> d.keys = 123
    ReadOnlyAttributeError                    Traceback (most recent call last)
    ...
    >>> d.f.g = 7
    AttributeError: 'NoneType' object has no attribute 'g'
    >>> d.a = {}
    ReadOnlyAttributeError: <class '__main__.ReadOnlyAttributeDict'>.a is read-only!
    >>> d.g = 7
    ReadOnlyAttributeError: <class '__main__.ReadOnlyAttributeDict'>.g is read-only!

    '''
    pass


class ReadOnlyAttributeDict(AttributeDict):
    __ro__ = False
    __marker__ = object()

    def __setitem__(self, key, value):
        if self.__ro__ is True:
            raise ReadOnlyAttributeError(
                "%s.%s is read only!" % (self.__class__, key))
        super(ReadOnlyAttributeDict, self).__setitem__(key, value)

    def __getitem__(self, key):
        # if item not found return self.__marker
        # value = self.get(key, self.__marker__)
        value = self.get(key, None)
        if isinstance(value, ReadOnlyAttributeDict):
            value.__ro__ = self.__ro__
        """
        # get rid of Attribute not found Exception
        if value is NewAttributeDict.__marker__:
            value = NewAttributeDict()
            self.__setitem__(key, value)
        """
        return value

    __getattr__ = __getitem__

    def json(self, allow_null=None, params=None):
        return json.dumps(self, cls=JSONEncoder)

    @property
    def nodes(self):
        '''
        get all url paths
        '''
        path = []
        print self
        for v in self.itervalues():
            if isinstance(v, self.__class__):
                path.extend(v.nodes)
            else:
                path.append(v)
        return path
        # return reduce(lambda x, y: x + y, (v.allpath if isinstance(v,
        # self.__class__) else [v] for v in self.__dict__.viewvalues()))


class Namespace(object):

    def __init__(self, params):
        for key, value in params.iteritems():
            if isinstance(value, dict):
                self.__dict__[key] = Namespace(value)
            else:
                self.__dict__[key] = value

    def __setattr__(self, name, value):
        raise ReadOnlyAttributeError(
            "%s.%s is read only!" % (self.__class__, name))

    @property
    def allpath(self):
        '''
        get all url paths
        '''
        return reduce(lambda x, y: x + y, (v.allpath if isinstance(v, Namespace) else [v] for v in self.__dict__.viewvalues()))
