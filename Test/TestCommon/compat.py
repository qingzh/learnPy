#! -*- coding:utf8 -*-

import requests
from functools import partial


__all__ = ['requests']

requests.Session.send = partial(requests.Session.send, verify=False)
