#! -*- coding:utf8 -*-

from threading import local as threading_local
from collections import defaultdict
from models.const import WIDTH
from models.const import API_STATUS


#---------------------------------------------------------------------------
#  Store results of test suite


class Local(threading_local):

    @property
    def results(self):
        if 'results' not in self.__dict__:
            self.__dict__['results'] = []
        return self.__dict__['results']

    @property
    def entries(self):
        if 'entries' not in self.__dict__:
            self.__dict__['entries'] = {}
        return self.__dict__['entries']

    @property
    def suites(self):
        if 'suites' not in self.__dict__:
            self.__dict__['suites'] = defaultdict(set)
        return self.__dict__['suites']

    @classmethod
    def _property_dec(cls, key, value):
        def fget(self):
            if key not in self.__dict__:
                self.__dict__[key] = value
            return self.__dict__[key]
        return fget

    @classmethod
    def _set_property(cls, key, value):
        setattr(cls, key, property(cls._property_dec(key, value)))

    def get_results(self):
        return self.results

    def clear_results(self):
        self.__dict__['results'][:] = []

    def print_results(self):
        results = self.results
        for i in results:
            print '-' * 100
            print i.pretty()
        else:
            print '-' * 100
        succeed = sum((x.status == API_STATUS.SUCCESS for x in results))
        print ('{:>%ds} : {:<d}' % WIDTH.DESCRIPTION).format(
            'SUCCESS', succeed)
        print ('{:>%ds} : {:<d}' % WIDTH.DESCRIPTION).format(
            'FAILED', len(results) - succeed)

    #-------------------------------------------------------------------------
    #
    #   我们以 server, username 作为 hash
    #
    #-------------------------------------------------------------------------

    def get_tag_dict(self, key, tagType):
        entries = self.entries
        # key: (server, username)
        # Be CARE: uid maybe integer
        if tagType not in entries.setdefault(key, {}):
            entries[key][tagType] = {}
        return entries[key][tagType]


ThreadLocal = Local()
