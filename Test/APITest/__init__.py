# -*- coding: utf-8 -*-
'''
Doing REST test takes a lot of time on the `data formats`,
and  the URIs are simple and well linked.

'''
from .compat import *
from .models import *
from .utils import *
from .settings import *

__title__ = 'APITest'
__version__ = '1.0.0'
__author__ = 'Qing Zhang'

__all__ = []

LOCKS = set()

ThreadLocal.__class__.SERVER = SERVERS.BETA
ThreadLocal.USER = USERS['wolongtest']