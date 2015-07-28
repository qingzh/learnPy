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
