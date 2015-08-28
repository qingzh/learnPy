#! -*- coding:utf8 -*-

'''
专注于测试customizedList接口
也就是cpc推广管理展示页面
包括：
  状态，排序，翻页
不包括：
  过滤

Sample:
# url path 由 context.bizParam.level 决定
# 页数由 context.bizParam.reqPageIndex 决定
# 筛选条件由 filterMapJson 决定
# 排序条件由 orderName, orderValue 决定
# 展示的数据层级又 context.bizParam.parentLevel 决定
r = requests.Request()
r.url = '%s%s' % (server, "/cpc/unit/customizedList.json")
r.data = {u'context': [
    u'{"bizParam":{"uid":"1061","level":3,"recordPerPage":"50","startDate":"2015-06-01","endDate":"2015-07-01","totalRecord":5,"reqPageIndex":1,"totalPage":1,"orderName":"consume","orderValue":"true","filterMapJson":{"frontState":"0"},"ids":"","parentLevel":1}}']}


说到底，和 API 测试是相仿的
区别
1. 输入数据的格式
2. url拼接是动态的

可以提供 一个Web界面，手动生成接口测试用例
但是没法 `固定的`验证返回数据

uri, 输入的json

'''


import requests
import sys
import json
from APITest.model.models import AttributeDict, TestRequest, APIData, _slots_class
from APITest.settings import api, USERS
from APITest.utils import write_file
import itertools
import re
import os
import xlrd
import logging
from APITest.model.models import log_stdout
import urlparse
from lxml import etree
from itertools import izip

##########################################################################
#   logging settings

__loglevel__ = logging.DEBUG

log = logging.getLogger(__name__)
log.setLevel(__loglevel__)
log_stdout.setLevel(__loglevel__)
log.addHandler(log_stdout)

_encode_params = requests.PreparedRequest._encode_params

##########################################################################
"""
准备 session, cookies
"""

headers = {
    # 'Connection': 'keep-alive',
    # 'Content-Length': '0',
    # 'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36',
}

# 前端传入的字段
orderName = {
    'acp': u'平均点击价格',
    'clickRatio': u'点击率',
    'consume': u'花费',
    'clickNum': u'点击次数',  # 后端返回 'click_num'
    'showNum': u'展现次数',
}

# 后端返回的字段
sortField = {
    'acp': u'平均点击价格',
    'clickRatio': u'点击率',
    'consumed': u'花费',
    'click_num': u'点击次数',  # 后端返回 'click_num'
    'show_num': u'展现次数',
}
orderValue = {
    True: u'升序',
    False: u'降序',
}

"""
准备 状态筛选
"""

# TODO: frontState 必须是字符串！！
# TODO: frontState 不能等于 null，只能不存在！！！
frontState = {
    # \wolong\website\admgmt\src\main\java\com\wolong\admgmt\service\impl\SpecEntityConvertor.java
    #
    #  0：计划暂停 > 1：推广账户预算不足> 2：推广计划预算不足
    #  > 3：暂停时段 > 4：推广中
    "plan": {
        None: u'显示全部',
        '0': u'计划暂停',
        '1': u'推广账户预算不足',
        '2': u'推广计划预算不足',
        '3': u'暂停时段',
        '4': u'推广中'
    },
    # 0：暂停推广 > 1：所属推广计划暂停 > 2：推广中
    "unit": {
        None: u'显示全部',
        '0': u'暂停推广',
        '1': u'所属推广计划暂停',
        '2': u'推广中',
    },
    # 前端展现状态
    # 0：暂停推广 > 1：审核中> 2：不宜推广 > 3：所属推广计划暂停 >
    # 4：所属推广单元暂停 > 5：出价过低 > 7：推广中
    #  Short frontState = 7;
    #   if (winfo.getIsPaused() == 1) {
    #    frontState = 0;  //暂停推广
    #   } else if (rsFront == 1) {
    #    frontState = 1;  //审核中
    #   } else if (rsFront == 2) {
    #    frontState = 2;  //不宜推广
    #   } else if (plan.getIsPaused() == 1) {
    #    frontState = 3;  // 所属推广计划暂停
    #   } else if (unit.getIsPaused() == 1) {
    #    frontState = 4;  // 所属推广单元暂停
    #   }
    "winfo": {
        None: u'显示全部',
        '0': u'暂停推广',
        '1': u'审核中',
        '2': u'不宜推广',
        '3': u'所属推广计划暂停',
        '4': u'所属推广单元暂停',
        '7': u'推广中',
    },
    # 0：暂停推广 > 1：审核中 > 2：不宜推广 > 3：所属推广计划暂停
    # > 4：所属推广单元暂停 > 5：推广中
    #  \wolong\website\common\src\main\java\com\wolong\spec\PhoneSpec.java
    "idea": {
        None: u'显示全部',
        '0': u'暂停推广',
        '1': u'审核中',
        '2': u'不宜推广',
        '3': u'所属推广计划暂停',
        '4': u'所属推广单元暂停',
        '5': u'推广中',
    },
    "ideaPro": {
        None: u'显示全部',
        '0': u'暂停推广',
        '1': u'审核中',
        '2': u'不宜推广',
        '3': u'所属推广计划暂停',
        '4': u'所属推广单元暂停',
        '5': u'推广中',
    },
    # 0：暂停推广 > 1：审核中 > 2：不宜推广 > 3：推广中
    #  \wolong\website\common\src\main\java\com\wolong\spec\PhoneSpec.java
    "phone": {
        None: u'显示全部',
        '0': u'暂停推广',
        '1': u'审核中',
        '2': u'不宜推广',
        '3': u'推广中',
    },
    #  \wolong\website\common\src\main\java\com\wolong\spec\XiJingSpec.java
    "xiJin": {
        None: u'显示全部',
        '0': u'暂停推广',
        '1': u'审核中',
        '2': u'不宜推广',
        '3': u'推广中',
    },
    # \wolong\website\common\src\main\java\com\wolong\spec\AppSpec.java
    "app": {
        None: u'显示全部',
        '0': u'暂停推广',
        '1': u'审核中',
        '2': u'不宜推广',
        '3': u'推广中',
    },
}
level_map = [None, 'user', 'plan', 'unit', 'winfo', 'idea', 'app',
             'phone', 'xiJin', 'ideaPro', 'ideaProPic', 'ideaProApp']


class Context(AttributeDict):
    __slots__ = ['context']
    # __init__ 会递归对 dict 对象套用 __class__
    __classhook__ = AttributeDict

    def __init__(self, *args, **kwargs):
        d = dict(*args, **kwargs)
        super(Context, self).__init__(context=[{
            "bizParam": {
                "uid": None,
                "level": None,
                "recordPerPage": 50,  # max = 500
                "startDate": None,
                "endDate": None,
                "totalRecord": -1,
                "reqPageIndex": 1,
                "totalPage": -1,
                "filterMapJson": {
                    # "frontState": None,  # 状态筛选
                },
                "orderName": None,
                "orderValue": None,  # False: Descend
                "ids": "",  # Keep it Blank
                "parentLevel": 1,  # `1`: account level
                "parentId": None,  # Keep it Blank at account level
                # TODO: 这里 onlyBatchIdList 也不能是None
                # 只能是 False 或者 True
                # "onlyBatchIdList": None  # True to get all child ids
            }}])
        self.bizParam.update(d)

    def __getattr__(self, key):
        if key == 'context':
            return AttributeDict.__getattr__(self, key)[0]
        elif key == 'bizParam':
            return self.context.bizParam
        else:
            return self.context.bizParam[key]

    def __setattr__(self, key, value):
        '''
        只在最外层有效
        >>> ct = Context()
        >>> ct.level = 123  # ct.context.bizParam.level
        >>> ct.context.abc = 123  # ct.context.abc
        '''
        if key == 'context':
            super(Context, self).__setattr__(key, value)
        elif key == 'bizParam':
            self.context.__setattr__(key, value)
        else:
            self.bizParam.__setattr__(key, value)

    def update(self, *args, **kwargs):
        d = dict(*args, **kwargs)
        for key, value in d.iteritems():
            self.__setattr__(key, value)

    def set_batch(self, value):
        '''
        @param value: boolean
        '''
        if value is None:
            self.bizParam.pop('onlyBatchIdList', None)
        else:
            self.onlyBatchIdList = value

    def set_level(self, level):
        self.level = level

    def set_uid(self, uid):
        self.uid = uid

    def set_order(self, orderName, orderValue):
        self.orderName = orderName
        self.orderValue = orderValue

    def set_page_index(self, index):
        self.reqPageIndex = index

    def set_state(self, state):
        if state is None:
            self.filterMapJson = {}
        else:
            self.filterMapJson = dict(frontState=state)

    def set_date(self, start, end):
        self.startDate = start
        self.endDate = end

    def prepare(self):
        return {'context': [self.context.json()]}


def _prepare_server(server):
    '''
    namedtuple('ParseResult', 'scheme netloc path params query fragment')
    '''
    parsed = list(urlparse.urlparse(server))
    parsed[0] = parsed[0] or 'http'
    if not parsed[1]:
        parsed[1] = parsed[2]
        parsed[2] = ''
    return urlparse.urlunparse(parsed)


class HttpServer(object):

    def __init__(self, session, server, username, password, headers=None):
        self.session = session
        self.server = server
        self.username = username
        self.password = password
        self.headers = headers
        self._assertion = True
        self.history = []

    @property
    def server(self):
        return self._server

    @server.setter
    def server(self, value):
        self._server = _prepare_server(value)

    def __repr__(self):
        return repr(self.__dict__)

    def set_cookies_from_driver(self, driver):
        for cookie in driver.get_cookies():
            if 'expiry' in cookie:
                cookie['expires'] = cookie.pop('expiry')
            self.session.cookies.set_cookie(
                requests.cookies.create_cookie(**cookie))

    def prepare_cookies(self):
        '''
        @param session: session
        @param server: server address
        @param username: username
        @param password: password
        @return `RequestsCookieJar`: cookies of login account
        '''
        r = self.session.get(self.server)
        assert r.status_code == 200, 'Failed to get page "%s": %d Error' % (
            self.server, r.status_code)
        page = etree.HTML(r.content)

        payload = {}
        for e in page.xpath('//input'):
            payload[e.get('name')] = e.get('value')
        payload.update(
            username=self.username,  password=self.password,  captchaResponse='1')

        res = self.session.post(
            r.url, verify=False, data=payload, headers=self.headers)
        assert 'login' not in res.url.lower(), 'Login failed!'

    @property
    def cookies(self):
        '''
        @return RequestsCookieJar: self.session.cookies
        '''
        if isinstance(self.session, requests.Session):
            return self.session.cookies
        return None

    def _assert_response(self, res, context):
        condition = res.json(object_hook=AttributeDict).data.queryCondition
        assert condition.userId == context.uid
        assert condition.currentPage == context.reqPageIndex
        assert condition.pageSize == context.recordPerPage
        # assert batch ids
        assert condition.isQueryAll == context.bizParam.get(
            'onlyBatchIdList', False)
        # assert filter
        # TODO: 这里返回的是 int，但是传入参数却要求是 string
        assert str(condition.get('state', None)) == str(context.filterMapJson.get(
            'frontState', None))
        # assert order
        assert condition.ascend == (
            context.bizParam.get('orderValue', None) is True)
        assert sortField.get(condition.get('sortField', None), None) == orderName.get(
            context.bizParam.get('orderName', None), None)

    def post(self, context, assertion=None):
        '''
        `POST` context to `customizedList.json`
        '''
        if assertion is None:
            assertion = self._assertion
        url = self._get_url(context.level)
        print url, self.headers
        res = self.session.post(
            url, data=context.prepare(), headers=self.headers)
        if assertion:
            self._assert_response(res, context)
        return res

    def _get_url(self, level):
        '''
        Produce the `customizedList.json` url

        | UserLevel | 1 | 账户 |
        | PlanLevel | 2 | 计划 |
        | UnitLevel | 3 | 单元|
        | WinfoLevel | 4 | 关键词 |
        | IdeaLevel | 5 | 创意 |
        | AppLevel | 8 | APP |
        | PhoneLevel | 9 | 电话 |
        | XiJingLevel | 10 | 蹊径 |
        '''
        # parsedUrl = urlparse.urlparse(server)
        # parsedUrl.scheme = parsedUrl.scheme or 'http'
        return urlparse.urljoin(
            self.server, '/cpc/%s/customizedList.json' % level_map[level])


class ServerInfo(object):

    def __init__(self, username, password, userid, server):
        self.username = username
        self.password = password
        self.userid = userid
        self.server = server

info_A = ServerInfo(u'携程旅行网', 'pd123456', 1061, '42.120.168.65')
info_B = ServerInfo(u'携程旅行网', 'pd123456', 1061, '42.120.172.21')

'''
USERNAME = 'ShenmaPM2.5'
PASSWORD = 'pd123456'
USERID = 1520
SERVER = 'https://e.sm.cn'
'''
# 日期区间：5月份
startDate = '2015-05-01'
endDate = '2015-06-01'

RE_LEVEL = re.compile(r'(/+)?cpc/+(?P<level>[^/]+)')


def format(res):
    level = RE_LEVEL.search(res.request.url).group('level')
    condition = res.json(object_hook=AttributeDict).data.queryCondition
    # context = urlparse.parse_qs(res.request.body)
    state = condition.get('state', None)
    state = frontState[level][None if state is None else str(state)]
    sortName = sortField.get(condition.get('sortField', None), u'默认排序')
    ascend = u'无' if sortName == u'默认排序' else orderValue[
        condition.get('ascend')]
    pageIndex = condition.currentPage
    totalSize = condition.totalSize
    # 层级，状态，排序条件，页数，响应时间，总数
    return ','.join([
        level, state, sortName + '-' + ascend, str(pageIndex),
        str(round(res.elapsed.total_seconds() * 1000, 2)), str(totalSize)])


def test_orderName(server, context):
    '''
    不包含默认排序
    排序需要 orderName 和 orderValue 同时存在
    如缺一，则还是默认排序
    '''
    for name in orderName:
        print orderName[name]
        for value in orderValue:
            context.set_order(name, value)
            server.history.append(server.post(context))


def assert_history(a_history, b_history):
    for a, b in izip(a_history, b_history):
        assert a.json() == b.json()


def server_decorator(func):
    def wrapper(server, context, *args, **kwargs):
        if isinstance(server, list):
            if not isinstance(context, list):
                raise Exception("`context` should be list!")
        else:
            return func(server, context, *args, **kwargs)
        for s, c in izip(server, context):
            func(s, c, * args, **kwargs)
        # Compare History
        for i in range(1, len(server)):
            assert_history(server[i].history, server[0].history)
    return wrapper


@server_decorator
def test_state_filter(server, context, order=False):
    state_map = frontState[level_map[context.level]]
    for state in state_map:
        print state_map[state]
        context.set_state(state)
        server.history.append(server.post(context))
        if order:
            test_orderName(server, context)


class TestObject(object):

    def __init__(self, info):
        self.context = Context(uid=info.userid)
        self.server = HttpServer(
            requests.Session(), info.server, info.username, info.password)

A = TestObject(info_A)
B = TestObject(info_B)


def compare_between_servers(a, b):
    '''
    path, query, timec
    '''
    a.context.update(level=3)
    a.context.set_date(startDate, endDate)

    b.context.update(level=3)
    b.context.set_date(startDate, endDate)
    # "显示全部"
    # entries.append(server.post(context))
    return a, b
