# -*- coding: utf-8 -*-
'''
Doing REST test takes a lot of time on the `data formats`,
and  the URIs are simple and well linked.

'''
from .models import *
from .compat import *
from .utils import *
from .settings import SERVERS, USERS


__title__ = 'APITest'
__version__ = '1.0.0'
__author__ = 'Qing Zhang'

ThreadLocal.SERVER = SERVERS.BETA


def userget(self):
    return self._user


def userset(self, value):
    if not isinstance(value, UserObject):
        value = UserObject(**value)
    self._user = value


ThreadLocal.__class__.USER = property(userget, userset)
ThreadLocal.USER = USERS['wolongtest']
