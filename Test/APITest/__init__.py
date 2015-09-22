# -*- coding: utf-8 -*-
'''
Doing REST test takes a lot of time on the `data formats`,
and  the URIs are simple and well linked.

'''
from .compat import *
from .models import *
from .utils import *
from .settings import *
from datetime import datetime

__title__ = 'APITest'
__version__ = '1.0.0'
__author__ = 'Qing Zhang'

__all__ = []


def userget(self):
    return self.__dict__['user']


def userset(self, value):
    if not isinstance(value, UserObject):
        value = UserObject(**value)
    self.__dict__['user'] = value


def timeset(self, value):
    self.__dict__['create_time'] = value.strftime(self._TIME_FORMAT)

def timeget(self):
    return self.__dict__['create_time']

def datetimeget(self):
    return datetime.strptime(
        self.__dict__['create_time'], self._TIME_FORMAT)


ThreadLocalClass = ThreadLocal.__class__
ThreadLocalClass._TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
ThreadLocalClass.USER = property(userget, userset)
ThreadLocalClass.create_time = property(timeget, timeset)
ThreadLocalClass.datetime = property(datetimeget)
ThreadLocal.SERVER = SERVERS.BETA
ThreadLocal.USER = USERS['wolongtest']

LOCKS = set()
