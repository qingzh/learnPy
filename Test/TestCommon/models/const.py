'''
store `const` in common
'''
import logging
import sys

STDOUT = logging.StreamHandler(sys.stdout)
STDOUT.setLevel(logging.DEBUG)

BLANK = object()


class STATUS(object):
    SUCCESS = 'PASS'
    FAILED = 'FAIL'
    EXCEPTION = 'ERROR'


class SUITE(object):
    API = 0


class WIDTH(object):
    DESCRIPTION = 76
    STATUS = 5
    RUNTIME = 6
