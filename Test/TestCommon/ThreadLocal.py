#! -*- coding:utf8 -*-

from threading import local

_thread_locals = local()
_thread_locals.entries = {}


#---------------------------------------------------------------------------
#  Store results of test suite

def get_results():
    if not hasattr(_thread_locals, 'results'):
        _thread_locals.results = []
    return getattr(_thread_locals, 'results')


def clear_results():
    _thread_locals.results[:] = []


def print_results():
    for i in get_results():
        print '-' * 100
        print i.pretty()
    else:
        print '-' * 100

#---------------------------------------------------------------------------


def get_url():
    return getattr(_thread_locals, 'url', 'http://www.shenma-inc.com')


def set_url(value):
    setattr(_thread_locals, 'url', value)


#---------------------------------------------------------------------------
#
#   我们以 server, username 作为 hash
#
#---------------------------------------------------------------------------

def get_tag_dict(key, tagType):
    # key: (server, username)
    # Be CARE: uid maybe integer
    if tagType not in _thread_locals.entries.setdefault(key, {}):
        _thread_locals.entries[key][tagType] = {}
    return _thread_locals.entries[key][tagType]
