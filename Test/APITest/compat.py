#! -*- coding:utf8 -*-

from TestCommon.decorators import *
from TestCommon.models.const import *
from TestCommon.models.common import *
from TestCommon.models.unittest import *
from TestCommon.exceptions import *
from TestCommon import ThreadLocal
from TestCommon.utils import is_sequence, gen_chinese_unicode
import logging
from datetime import datetime
from .models.user import UserObject
from functools import update_wrapper
from APITest.models import models


FORMATTER = logging.Formatter('[%(module)s:%(funcName)s] %(message)s')


def log_dec(log, filename, level=logging.DEBUG):
    def decorator(func):
        def wrapper(*args, **kwargs):
            output_file = logging.FileHandler(filename, 'a')
            output_file.setLevel(level)
            output_file.setFormatter(FORMATTER)
            log.addHandler(output_file)
            models.log.addHandler(output_file)

            ret = func(*args, **kwargs)

            models.log.removeHandler(output_file)
            log.removeHandler(output_file)
            return ret
        return update_wrapper(wrapper, func)
    return decorator


def userget(self):
    return self.user


def userset(self, value):
    if not isinstance(value, UserObject):
        value = UserObject(**value)
    self.user = value


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
