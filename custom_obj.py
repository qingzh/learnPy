# -*- coding: utf-8 -*-


class ReadOnlyAttributeError(Exception):
    pass


class ReadOnlyObject(object):

    def __setattr__(self, name, value):
        raise ReadOnlyAttributeError(
            "%s.%s is read only!" % (self.__class__, name))
    __setitem__ = __setattr__


class AttributeDict(dict):

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, AttributeDict):
            value = AttributeDict(value)
        super(AttributeDict, self).__setitem__.(self, key, value)

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        return ReadOnlyAttributeDict(value) if isinstance(value, dict) else value
    __getattr__ = __getitem__

    '''
    def __init__(self, *args, **kwargs):
        """
        not work for iter dict
        """
        super(ReadOnlyAttributeDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
    '''
    '''
    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        return ReadOnlyAttributeDict(value) if isinstance(value, dict) else value
    __getattr__ = __getitem__
    '''


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
