#! -*- coding:utf8 -*-

from threading import local as threading_local
from collections import defaultdict
from .models.const import WIDTH, API_STATUS
import logging

__all__ = ['ThreadLocal']
# --------------------------------------------------------------------------
#  Store results of test suite


PATTERN = """Test method:{name}({module})
this is the {idx} testcase\n
case description: {desc}
{log}
Runtime is: {time}
"""


def format_time(f):
    ''' f: float '''
    h = f / 3600
    m = (f - h * 3600) / 60
    s = f % 60
    return '%d hours %d minutes %.2f seconds' % (h, m, s)


class Local(threading_local):

    LOG_LEVEL = logging.DEBUG

    def lock(self):
        self._lock = True

    def unlock(self):
        self._lock = False

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

    def new_results(self):
        self.__dict__['results'] = []

    def clear_results(self):
        self.__dict__['results'][:] = []

    def print_results(self):
        results = self.results
        for i in results:
            print self.SEPERATOR_LINE
            print i.pretty()
        else:
            print self.SEPERATOR_LINE
        succeed = sum((x.status == API_STATUS.SUCCESS for x in results))
        print ('{:>%ds} : {:<d}' % WIDTH.DESCRIPTION).format(
            'SUCCESS', succeed)
        print ('{:>%ds} : {:<d}' % WIDTH.DESCRIPTION).format(
            'FAILED', len(results) - succeed)

    SEPERATOR_LINE = '-' * 90

    def print_details(self, t=API_STATUS.FAILURE):
        results = self.results
        total = 0
        for i in results:
            if i.status < t:
                continue
            total += 1
            print self.SEPERATOR_LINE
            print i.description
            print '.' * 80
            print i.message
        else:
            print self.SEPERATOR_LINE
        print 'Total: %d' % total

    def format_with_ruby(self):
        results = self.results
        print '# Runing tests:\n'
        strlist = []
        failtotal = errtotal = 0
        for idx, r in enumerate(results):
            if r.status == API_STATUS.FAILURE:
                prefix = 'compare fail!'
                failtotal = failtotal + 1
            elif r.status == API_STATUS.EXCEPTION:
                prefix = 'error'
                errtotal = errtotal + 1
            else:
                prefix = 'success'
            strlist.append(PATTERN.format(
                name=r.function,
                module=r.module,
                idx=idx,
                desc=r.description.strip(),
                log=' '.join((prefix, r.message.strip())),
                time=format_time(r.runtime),
            ))
        print '.'.join(strlist)
        print '%d tests, %d assertions, %d failures, %d errors, %d skips' % (
            len(results), 0, failtotal, errtotal, 0)

    # ---------------------------------------------------------------------
    #
    #   我们以 server, username 作为 hash
    #
    # ---------------------------------------------------------------------

    def get_tag_dict(self, key, tagType):
        entries = self.entries
        # key: (server, username)
        # Be CARE: uid maybe integer
        if tagType not in entries.setdefault(key, {}):
            entries[key][tagType] = {}
        return entries[key][tagType]


ThreadLocal = Local()
