# -*- coding: utf-8 -*-


class ReadOnlyAttributeError(Exception):
    pass


class ReadOnlyObject(object):

    def __setitem__(self, key, value):
        raise ReadOnlyAttributeError(
            "%s.%s is read-only!" % (self.__class__, key))
    __setattr__ = __setitem__


class ReadOnlyAttributeDict(ReadOnlyObject, dict):

    '''
    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        return ReadOnlyAttributeDict(value) if isinstance(value, dict) else value
    __getattr__ = __getitem__
    '''

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


class AttrDict(dict):

    '''
    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        return ReadOnlyAttributeDict(value) if isinstance(value, dict) else value
    __getattr__ = __getitem__
    '''

    def __init__(self, *args, **kwargs):
        """
        take care of nested dict
        """
        super(AttrDict, self).__init__(*args, **kwargs)
        super(AttrDict, self).__setattr__('__dict__', self)
        for key, value in self.iteritems():
            if isinstance(value, dict) and not isinstance(value, AttrDict):
                super(AttrDict, self).__setitem__(
                    key, AttrDict(value))


class ReadOnlyAttrDict(ReadOnlyObject, AttrDict):

    '''
    we expect nested AttrDict to be ReadOnlyAttrDict ...
    '''
    pass


class AttributeDict(dict):
    __ro__ = False

    def __init__(self, *args, **kwargs):
        super(AttributeDict, self).__init__(*args, **kwargs)
        for key, value in self.iteritems():
            if isinstance(value, dict) and not isinstance(value, AttributeDict):
                self[key] = AttributeDict(value)

    def __setitem__(self, key, value):
        if self.__ro__ is True:
            raise ReadOnlyAttributeError(
                "%s.%s is read only!" % (self.__class__, key))
        if isinstance(value, dict) and not isinstance(value, AttributeDict):
            value = AttributeDict(value)
        super(AttributeDict, self).__setitem__(key, value)

    '''

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        return ReadOnlyAttributeDict(value) if isinstance(value, dict) else value
    '''
    __getattr__ = dict.__getitem__

    def __setattr__(self, key, value):
        """
        字典里不允许存在类默认的属性
        例如：iterkeys, __dict__ 之类
        """
        if key in dir(dict):
            raise ReadOnlyAttributeError(
                "%s.%s is read-only!" % (self.__class__, key))
        if key in vars(AttributeDict):
            super(AttributeDict, self).__setattr__(key, value)
        else:
            self.__setitem__(key, value)

    def read_only(self, allow):
        self.__ro__ = allow


class NewAttributeDict(dict):
    __ro__ = False
    __marker__ = object()

    def __init__(self, *args, **kwargs):
        super(NewAttributeDict, self).__init__(*args, **kwargs)
        for key, value in self.iteritems():
            if isinstance(value, dict) and not isinstance(value, NewAttributeDict):
                self[key] = NewAttributeDict(value)

    def __setitem__(self, key, value):
        if self.__ro__ is True:
            raise ReadOnlyAttributeError(
                "%s.%s is read only!" % (self.__class__, key))
        if isinstance(value, dict) and not isinstance(value, NewAttributeDict):
            value = NewAttributeDict(value)
        super(NewAttributeDict, self).__setitem__(key, value)

    '''

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        return ReadOnlyAttributeDict(value) if isinstance(value, dict) else value
    '''

    def __getitem__(self, key):
        # if item not found return self.__marker
        value = self.get(key, NewAttributeDict.__marker__)
        if isinstance(value, NewAttributeDict):
            value.__ro__ = self.__ro__
        """
        # get rid of Attribute not found Exception
        if value is NewAttributeDict.__marker__:
            value = NewAttributeDict()
            self.__setitem__(key, value)
        """
        return value

    __getattr__ = __getitem__

    def __setattr__(self, key, value):
        if key in dir(dict):
            raise ReadOnlyAttributeError(
                "%s.%s is read-only!" % (self.__class__, key))
        if key in vars(NewAttributeDict):
            super(NewAttributeDict, self).__setattr__(key, value)
        else:
            self.__setitem__(key, value)


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
