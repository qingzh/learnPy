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
r.data = {u'context': [u'{"bizParam":{"uid":"1061","level":3,"recordPerPage":"50","startDate":"2015-06-01","endDate":"2015-07-01","totalRecord":5,"reqPageIndex":1,"totalPage":1,"orderName":"consume","orderValue":"true","filterMapJson":{"frontState":"0"},"ids":"","parentLevel":1}}']}

'''


import requests
import sys
import json
from APITest.model.models import AttributeDict, TestRequest, APIData, _slots_class
from APITest.settings import api, USERS
from APITest.utils import prepare_cookies, write_file
import itertools
import re
import os
import xlrd
import logging
from APITest.model.models import log_stdout
import urlparse

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log_stdout.setLevel(logging.DEBUG)
log.addHandler(log_stdout)

_encode_params = requests.PreparedRequest._encode_params
request = TestRequest()

###########################################################################
"""
准备 session, cookies
"""

a_server = ''
b_server = ''
headers = {
    'Connection': 'keep-alive',
    'Content-Length': '0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36',
}

USERNAME = u''
PASSWORD = ''
USERID = 1061

alpha = AttributeDict(session=requests.Session(), server=a_server)
beta = AttributeDict(session=requests.Session(), server=b_server)
a_cookies = prepare_cookies(
    username=USERNAME, password=PASSWORD, headers=headers, **alpha)
b_cookies = prepare_cookies(
    username=USERNAME, password=PASSWORD, headers=headers, **beta)

# 日期区间：5月份
startDate = '2015-05-01'
endDate = '2015-06-01'
orderName = ['acp', 'clickRatio', 'consume', 'clickNum', 'showNum']

context = AttributeDict({
    "context": {
        "bizParam": {
            "uid": None,
            "level": None,
            "recordPerPage": 50,  # max = 500
            "startDate": startDate,
            "endDate": endDate,
            "totalRecord": -1,
            "reqPageIndex": 1,
            "totalPage": -1,
            "filterMapJson": {
                # "frontState": 状态筛选
            },
            "orderName": None,
            "orderValue": None,  # False: Descend
            "ids": "",  # Keep it Blank
            "parentLevel": 1,  # `1`: account level
            "parentId": None  # Keep it Blank at account level
        }}
})
context.bizParam.uid = USERID

"""
准备 状态筛选
"""

frontState = {
    # \wolong\website\admgmt\src\main\java\com\wolong\admgmt\service\impl\SpecEntityConvertor.java
    #
    #  0：计划暂停 > 1：推广账户预算不足> 2：推广计划预算不足
    #  > 3：暂停时段 > 4：推广中
    "plan": [0, 1, 2, 3, 4],
    # 0：暂停推广 > 1：所属推广计划暂停 > 2：推广中
    "unit": [0, 1, 2],
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
    "winfo": [0, 1, 2, 3, 4, 7],
    # 0：暂停推广 > 1：审核中 > 2：不宜推广 > 3：所属推广计划暂停
    # > 4：所属推广单元暂停 > 5：推广中
    #  \wolong\website\common\src\main\java\com\wolong\spec\PhoneSpec.java
    "idea": [0, 1, 2, 3, 4, 5],
    "ideaPro": [0, 1, 2, 3, 4, 5],
    # 0：暂停推广 > 1：审核中 > 2：不宜推广 > 3：推广中
    #  \wolong\website\common\src\main\java\com\wolong\spec\PhoneSpec.java
    "phone": [0, 1, 2, 3],
    #  \wolong\website\common\src\main\java\com\wolong\spec\XiJingSpec.java
    "xiJin": [0, 1, 2, 3],
    # \wolong\website\common\src\main\java\com\wolong\spec\AppSpec.java
    "app": [0, 1, 2, 3],
}

level_uri = [None, 'user', 'plan', 'unit', 'winfo', 'idea', 'app',
             'phone', 'xijing', 'ideaPro', 'ideaProPic', 'ideaProApp']


def set_uid(context, uid):
    context.bizParam.uid = uid


def set_order(context, orderName, orderValue):
    context.bizParam.orderName = orderName
    context.bizParam.orderValue = orderValue


def set_page_index(context, index):
    context.bizParam.reqPageIndex = index


def set_status(context, state):
    context.bizParam.filterMapJson = dict(frontState=state)


def set_url(server, level):
    '''
    | UserLevel | 1 | 账户 |
    | PlanLevel | 2 | 计划 |
    | UnitLevel | 3 | 单元|
    | WinfoLevel | 4 | 关键词 | 
    | IdeaLevel | 5 | 创意 |
    | AppLevel | 8 | APP |
    | PhoneLevel | 9 | 电话 |
    | XiJingLevel | 10 | 蹊径 |
    '''
    return server + '/' + level_uri[level] + '/customizedList.json'
