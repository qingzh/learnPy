# -*- coding:utf-8 -*-

from .utils import prepare_cookies
from requests import Session
import json
from .model.models import AttributeDict


class SuperUser(object):
    username = None
    userid = None
    session = None
    password = None

    def __init__(self, server, session=None):
        self.server = server
        self.session = session or Session()
        prepare_cookies(
            username=self.username, password=self.password,
            session=self.session, server=server)
        self.cookies = self.session.cookies


class Sales(SuperUser):
    username = u'销售管理'
    password = 'pd123456'
    userid = 689

    def get_sales(self, uid):
        res = self.session.get(
            self.server + '/sales/parentmgr', params=dict(uid=self.userid, userId=uid))
        return res

    def assign(self, uid, sales=1995):
        '''
        assign `sales` to `uid`
        '''
        parent = json.loads(
            self.get_sales(uid).content, object_hook=AttributeDict)
        if parent.data is not None:
            return parent.data
        body = dict(salesMgrId=sales, userIds=[uid])
        res = self.session.post(
            self.server + '/sales/assignment', params=dict(uid=self.userid), json=body)
        return res


class Customer(SuperUser):
    username = u'客服管理'
    password = 'pd123456'
    userid = 1562

    def get_customer(self, uid):
        res = self.session.get(
            self.server + '/sales/parentsales', params=dict(uid=self.userid, userId=uid))
        return res

    def assign(self, uid, customer=1161):
        '''
        assign `sales` to `uid`
        '''
        parent = json.loads(
            self.get_customer(uid).content, object_hook=AttributeDict)
        if parent.data is not None:
            return parent.data
        body = dict(custMgrId=customer, userIds=[uid])
        res = self.session.post(
            self.server + '/sales/customerassign', params=dict(uid=self.userid), json=body)
        return res
