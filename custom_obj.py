# -*- coding: utf-8 -*-

"""

"""

import json
from itertools import chain

SEQUENCE_TYPE = (list, tuple, set)


class TT(object):
    __slots__ = ['ab', 'bc']


class ImmutableError(Exception):
    pass


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

    def __setattr__(self, key, value):
        if key in dir(self.__class__):
            super(ReadOnlyObject, self).__setattr__(key, value)
        else:
            raise ReadOnlyAttributeError(
                "%s.%s is read-only!" % (self.__class__, key))


class PersistentAttributeObject(object):
    __marker__ = object()

    def __setitem__(self, key, value):
        if getattr(self, key, self.__marker__) is self.__marker__:
            raise KeyError(
                "%s.%s is not exist!" % (self.__class__, key))
        super(PersistentAttributeObject, self).__setitem__(key, value)

    def __setattr__(self, key, value):
        if key in dir(self.__class__):
            super(ReadOnlyObject, self).__setattr__(key, value)
        else:
            PersistentAttributeDict.__setitem__(self, key, value)

    def __delitem__(self, key):
        raise ReadOnlyAttributeError(
            "%s.%s is read-only!" % (self.__class__, key))

    __delattr__ = __delitem__

'''
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
'''


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
        for key, value in self.iteritems():
            # Nested AttributeDict object
            # new object should be instance of self.__class__
            AttributeDict.__setitem__(self, key, value)

    def __getattr__(self, key):
        ''' What's the difference vs.
        __getattr__ = dict.__getitem__
        '''
        return super(self.__class__, self).__getitem__(key)

    def __setitem__(self, key, value):
        # Nested AttributeDict object
        if isinstance(value, dict) and not isinstance(value, self.__class__):
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
            # TODO: trap here? `self` or `super`
            # What's the difference vs.
            # self.__setitem__(key, value)
            AttributeDict.__setitem__(self, key, value)

    def __call__(self, *args, **kwargs):
        '''

        self.update(...)
        '''
        super(AttributeDict, self).update(*args, **kwargs)
        return self

    def json(self, allow_null=None, filter=None, header=False):
        '''
        return json-formated string
        '''
        return json.dumps(self)

    @property
    def nodes(self):
        '''
        get all url paths
        '''
        path = []
        for v in self.itervalues():
            if isinstance(v, AttributeDict):
                path.extend(v.nodes)
            else:
                path.append(v)
        return path
        # return reduce(lambda x, y: x + y, (v.allpath if isinstance(v,
        # self.__class__) else [v] for v in self.__dict__.viewvalues()))


class PersistentAttributeDict(PersistentAttributeObject, AttributeDict):

    '''
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

    >>> d = PersistentAttributeDict(attr_dict)
    >>> d.g = 7
    ReadOnlyAttributeError: <class '__main__.ReadOnlyAttributeDict'>.g is not exist!
    >>> d.a = [1,2,3]
    >>> d.b.d.e = 2015
    {'a': [1, 2, 3], 'b': {'c': 3, 'd': {'e': 2015}}, 'f': None}
    >>> d.b.d.h = 8
    ReadOnlyAttributeError: <class '__main__.ReadOnlyAttributeDict'>.h is not exist!
    '''
    # Same as KeyImmutableDict possibly
    pass


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

'''
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
'''


class ImmutableDict(dict):

    def pop(self, key, value=None):
        raise ImmutableError('Immutable Dict!')

    def popitem(self):
        raise ImmutableError('Immutable Dict!')

    def __delitem__(self, key):
        raise ReadOnlyAttributeError(
            "%s.%s is read-only!" % (self.__class__, key))


class KeyImmutableDict(ImmutableDict, AttributeDict):

    """
    keys of the dict are immutable
    value of key is mutable
    """
    # attr0 = 0  # test __getattr__
    # attr1 = 1

    def __setattr__(self, key, value):
        # only defined attributes and items allowed
        print '__setattr__', key, value
        if key in self:
            super(KeyImmutableDict, self).__setitem__(key, value)
        elif hasattr(self, key):
            super(KeyImmutableDict, self).__setattr__(key, value)
        else:
            raise KeyError("%s.%s is not defined!" % (self.__class__, key))

    __setitem__ = __setattr__

    def update(self, *args, **kwargs):
        _dict = dict(*args, **kwargs)
        if set(_dict).issubset(self) is False:
            raise KeyError("Can NOT add key into %s!" % (self.__class__))
        for key in _dict.iterkeys():
            super(KeyImmutableDict, self).__setitem__(key, _dict[key])


class SlotsMeta(type):

    def __new__(cls, name, bases, attrs):
        print 'SlotsMeta __new__', name
        # attrs maybe a list
        if isinstance(attrs, SEQUENCE_TYPE):
            attrs = dict.fromkeys(attrs, None)
        attrs['__slots__'] = tuple(attrs)
        return super(SlotsMeta, cls).__new__(cls, name, bases, attrs)


class SlotsDict(KeyImmutableDict):

    def __init__(self, *args, **kwargs):
        # TODO: not compatible with nested dict
        _dict = {}
        for key in self.__slots__:
            _dict[key] = getattr(self.__class__, key, None)
        super(SlotsDict, self).__init__(_dict)
        super(SlotsDict, self).update(*args, **kwargs)


def _slots_class(name, attributes):
    '''
    Solid attributes
    '''
    return SlotsMeta(name, (SlotsDict,), attributes)


class OldSlotsDict(AttributeDict):

    __metaclass__ = SlotsMeta

    def dict(self):
        slots = chain.from_iterable(
            getattr(cls, '__slots__', []) for cls in self.__class__.__mro__)
        _dict = {}
        for key in slots:
            value = getattr(self, key, None)
            if hasattr(value, 'dict'):
                value = value.dict()
            _dict[key] = value
        return _dict

    def __str__(self):
        return json.dumps(self.dict())


class Namespace(object):

    def __init__(self, params):
        for key, value in params.iteritems():
            if isinstance(value, dict):
                self.__dict__[key] = Namespace(value)
            else:
                self.__dict__[key] = value

    def __setattr__(self, name, value):
        raise ReadOnlyAttributeError(
            "%s is read only!" % (self.__class__))

    @property
    def allpath(self):
        '''
        get all url paths
        '''
        return reduce(lambda x, y: x + y, (v.allpath if isinstance(v, Namespace) else [v] for v in self.__dict__.viewvalues()))
