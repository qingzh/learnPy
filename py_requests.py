
# -*- coding:utf-8 -*-

'''
ways to change `json.dumps` in requests
'''
from json import JSONEncoder


class MyEncoder(JSONEncoder):

    def default(self, obj):
        if hasattr(obj, 'dict'):
            return obj.dict()
        super(MyEncoder, self).default(obj)


def json_dump_decorator(func):
    def json_dump_wrapper(*args, **kwargs):
        kwargs['cls'] = MyEncoder
        print args
        print kwargs
        return func(*args, **kwargs)
    return json_dump_wrapper


def test(c):
    print c
    req = c(url='http://google.com', json=DATA())
    preq = req.prepare()
    print preq.body


class DATA(object):

    def dict(self):
        return {'test': 'hello', 'name': __file__}


def test_a():
    from requests import models

    class ARequest(models.Request):
        pass

    try:
        test(ARequest)
    except Exception as e:
        print e


"""
change variable `models.json_dumps`
and you should customize Request Object
"""


def test_c():
    from requests import models
    from json import dumps

    models.json_dumps = json_dump_decorator(dumps)

    class CRequest(models.Request):
        pass

    try:
        test(CRequest)
    except Exception as e:
        print e
