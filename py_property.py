import logging
from TestCommon.models.const import STDOUT

log = logging.getLogger('st')
log.setLevel(logging.DEBUG)
log.addHandler(STDOUT)

#############################################################


class PClass(object):

    def __get__(self, obj, objtype):
        ''' PClass __get__ '''
        log.debug('__get__: %s', locals())
        return self.abc

    def __set__(self, obj, value):

        raise AttributeError('Immutable!')

    def __init__(self, abc="test"):
        self.abc = abc

    def set(self, value):
        self.abc = value

    def __getattr__(self, key):
        self.testattr = 'testattr'
        if super(PClass, self).__getattribute__(key):
            return getattr(self, key)
        else:
            return 'ERROR to GET'


class Test(object):
    PROFILE = None

    @property
    def profile(self):
        print 'get profile of %s' % self
        return self.PROFILE

    @profile.setter
    def profile(self, value):
        print 'set profile of %s' % self
        if isinstance(value, int):
            self.PROFILE = 'int: %s' % value
        else:
            self.PROFILE = value

    def try_profile(self, value):
        print 'try profile of %s' % self
        # Do NOT use self.profile(value)
        a.__class__.__dict__['profile'].__set__(self, value)


class SubTest(Test):

    profile = Test.profile

'''
class PClass(object):

    def __init__(self, value):
        self._root = value

    @property
    def root(self):
        return self._root


class Son(PClass):

    @root.setter
    def root(self, value):
        self._root = value
'''

'''
class PClass(object):

    def __init__(self, value):
        self._root = value

    def fget(self):
        return self._root

    root = property(fget)


class Son(PClass):

    def fset(self, value):
        self._root = value

    root = property(fget, fset)
'''

#############################################################
# List of Property


class PClass(object):

    def __init__(self, value):
        self._abc = value

    def __get__(self, obj, objtype=None):
        print 'PClass __get__'
        return self._abc

    def __set__(self, obj, value):
        print 'PClass __set__'
        self._abc = value


class LClass(list):

    def __init__(self, *args, **kwargs):
        super(LClass, self).__init__(*args, **kwargs)
        self.root = object()

    def __getitem__(self, key):
        item = super(LClass, self).__getitem__(key)
        if hasattr(item, '__get__'):
            return item.__get__(self.root, type(self.root))
        else:
            return item

    def __setitem__(self, key, value):
        item = super(LClass, self).__getitem__(key)
        if hasattr(item, '__get__'):
            item.__set__(self.root, value)
        else:
            super(LClass, self).__setitem__(key, value)

l = LClass(PClass(i) for i in range(5))

""" %doctest_mode
>>> l.extend([1,3])
>>> l
[<__main__.PClass object at 0x6fffec3b550>, <__main__.PClass object at 0x6fffec3b590>, <__main__.PClass object at 0x6fffec3b5d0>, <__main__.PClass object at 0x6fffec3b610>, <__main__.PClass object at 0x6fffec3b650>, 1, 3]
>>> l[5] = 23
>>> l[3] = 'abc'
PClass __set__
>>> l
[<__main__.PClass object at 0x6fffec3b550>, <__main__.PClass object at 0x6fffec3b590>, <__main__.PClass object at 0x6fffec3b5d0>, <__main__.PClass object at 0x6fffec3b610>, <__main__.PClass object at 0x6fffec3b650>, 23, 3]
>>> l[1]
PClass __get__
1
>>>
"""

#############################################################


class Property(object):

    "Emulate PyProperty_Type() in Objects/descrobject.c"

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)

    def getter(self, fget):
        return type(self)(fget, self.fset, self.fdel, self.__doc__)

    def setter(self, fset):
        return type(self)(self.fget, fset, self.fdel, self.__doc__)

    def deleter(self, fdel):
        return type(self)(self.fget, self.fset, fdel, self.__doc__)
