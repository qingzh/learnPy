# -*- coding:utf-8 -*-s
from .models import _slots_class

__all__ = ['bulkJobRequestType']

bulkJobRequestType = _slots_class('bulkJobRequestType', dict(
    campaignIds=None,
    singleFile=None,
    format=None,
    variableColumns=None,
    fileController=None
))

'''
def __init__(obj, *args, **kwargs):
    obj.bulkJobRequestType = bulkJobRequestBody(*args, **kwargs)


def __setitem__(obj, key, value):
    obj.bulkJobRequestType.__setitem__(key, value)


def __getitem__(obj, key):
    return obj.bulkJobRequestType.__getitem__(key)


bulkJobRequestType = _slots_class('bulkJobRequestType', dict(
    bulkJobRequestType=None,
    __init__=__init__,
    __setitem__=__setitem__,
    __getitem__=__getitem__,
    __getattr__=__getitem__
))
'''

mask = (1 << 10) - 1


def iter_fileController(obj):
    for i in range(1, 10):
        new_obj = obj.copy()
        new_obj.fileController = mask ^ (1 << i)
        yield new_obj

setattr(bulkJobRequestType, 'iter_fileController', iter_fileController)
