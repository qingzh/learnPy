#! -*- coding:utf8 -*-

'''
from .models import *
: Initialize by models.__init__
compat 是用来修改 第三方模块的属性
所以应该放在最前面
'''
from .compat import *
from .models import *
from .threadlocal import *


'''
我们在compat里自定义了logging， 并进行了 import

print locals().keys()  # 查看本级目录下的环境

在TestCommon这个包下，所有的.py进行
import logging
时，得到的都是封装后的logging
这是由 import 的优先级顺序决定的，优先 import 本级目录下的文件

'''

__version__ = 1.0
__author__ = 'Qing Zhang'
