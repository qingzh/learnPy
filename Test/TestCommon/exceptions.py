#! -*- coding:utf8 -*-


class UndefinedException(Exception):
    pass


class ReadOnlyAttributeError(Exception):
    pass

class DBQueryException(Exception):
    pass