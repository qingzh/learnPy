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
from APITest.compat import AttributeDict, STDOUT
import re
import logging
from itertools import izip
from TestCommon.models.httplib import ServerInfo, HttpServer
##########################################################################
#   logging settings

__loglevel__ = logging.DEBUG

log = logging.getLogger(__name__)
log.setLevel(__loglevel__)
STDOUT.setLevel(__loglevel__)
log.addHandler(STDOUT)

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
level_map = {
    'user': 1,
    'plan': 2,
    'unit': 3,
    'winfo': 4,
    'idea': 5,
    'app': 6,
    'phone': 7,
    'xiJin': 8,
    'ideaPro': 9,
    'ideaProPic': 10,
    'ideaProApp': 11}

level_map_reversed = {
    1: 'user',
    2: 'plan',
    3: 'unit',
    4: 'winfo',
    5: 'idea',
    6: 'app',
    7: 'phone',
    8: 'xiJin',
    9: 'ideaPro',
    10: 'ideaProPic',
    11: 'ideaProApp'}


def _assert_response(res, context):
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
        try:
            level = int(level)
            self.level = level
        except ValueError:
            self.level = level_map.get(level.lower())

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

    @property
    def uri(self):
        return level_map_reversed.get(self.level)


info_A = ServerInfo('smdev', 'smdevsmdev', 1061, 'e.sm.cn')
info_B = ServerInfo('smdev', 'smdevsmdev', 1061, '42.120.172.21')

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
    path, query, time
    设置了层级
    '''
    a.context.update(level=3)
    a.context.set_date(startDate, endDate)

    b.context.update(level=3)
    b.context.set_date(startDate, endDate)
    # "显示全部"
    # entries.append(server.post(context))
    return a, b


def test(uid, s):
    context = Context(uid=uid)
    context.set_date(startDate, endDate)
    context.set_level('plan')
    context.recordPerPage = 500
    # 不排序
    # yield s.post(context)
    for order in orderName.keys():
        for value in orderValue.keys():
            context.set_order(order, value)
            yield s.post(context)


def _compare_dict(a, b):
    for key, value in a.iteritems():
        if value is None or key not in b:
            continue
        assert value == b[key], 'Content Differ at key `%s`!\nExpected: %s\nActually: %s\n' % (
            key, a, b)
    return True

import urlparse


def compare(uid, s_list):
    g_list = []
    for s in s_list:
        g_list.append(test(uid, s))

    g_base = g_list.pop()
    while True:
        r_base = next(g_base, None)
        if r_base is None:
            break
        d_base = r_base.json(object_hook=AttributeDict)
        for g in g_list:
            r = next(g)
            assert r.request.body == r_base.request.body, '%s != %s' % (
                r.request.body, r_base.request.body)
            print urlparse.parse_qs(r.request.body)
            d = r.json(object_hook=AttributeDict)
            assert d.status == d_base.status, '%s != %s' % (
                d.status, d_base.status)
            _compare_dict(d_base.data.queryCondition, d.data.queryCondition)
            all(_compare_dict(x, y)
                for x, y in izip(d_base.data.target, d.data.target))


def post(self, context, assertion=None):
    '''
    `POST` context to `customizedList.json`
    '''
    if assertion is None:
        assertion = self._assertion
    url = self._get_url(context)
    res = self.session.post(
        url, data=context.prepare(), headers=self.headers, verify=False)
    if assertion:
        for func in self._assertion:
            func(res, context)
    return res

HttpServer.post = post
