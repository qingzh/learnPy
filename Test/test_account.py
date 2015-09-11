# -*- coding:utf-8 -*-
'''
针对 附加创意 (NewCreative) 接口的回归测试:
'''
__version__ = 1.0
__author__ = 'Qing Zhang'

from APITest.models.models import (APIData, AttributeDict)
from TestCommon.models.const import STDOUT, BLANK
from APITest.models.account import *
from APITest.settings import SERVER, USERS, api, LOG_DIR
from APITest import settings
from APITest.utils import assert_header
from APITest.compat import formatter
from APITest.models.user import UserObject
from APITest.models.const import STATUS
from TestCommon import ThreadLocal
from TestCommon.exceptions import UndefinedException
import threading
from datetime import datetime
import logging
from TestCommon.utils import gen_chinese_unicode
import urlparse


##########################################################################
#    log settings

TAG_TYPE = u'账户'
TIMESTAMP = datetime.now().strftime('%Y%m%d%H%M%S%f')
LOG_DIR = r'.'
LOG_FILENAME = '%s/%s_%s.log' % (LOG_DIR, TAG_TYPE, TIMESTAMP)

__loglevel__ = logging.INFO
log = logging.getLogger(__name__)
log.setLevel(__loglevel__)
STDOUT.setLevel(__loglevel__)
log.addHandler(STDOUT)

output_file = logging.FileHandler(LOG_FILENAME, 'w')
output_file.setLevel(__loglevel__)
log.addHandler(output_file)

##########################################################################

DEFAULT_USER = UserObject(**USERS.get('wolongtest'))


'''
"account": {
    "getAccount": APIRequest(method=post, uri='/api/account/getAccount'),
    "updateAccount": APIRequest(method=post, uri='/api/account/updateAccount'),
}
'''
locals().update(api.account)

#-------------------------------------------------------------------------
# 准备测试数据
# description 总长
# 字典里存的是json形式，因为list不能hash
#-------------------------------------------------------------------------

_local_ = threading.local()
GLOBAL = _local_.__dict__.setdefault('global', {})
GLOBAL[TAG_TYPE] = {}

#-------------------------------------------------------------------------


def _compare_dict(a, b):
    for key, value in a.iteritems():
        if value is None:
            continue
        assert value == b[key], 'Content Differ at key `%s`!\nExpected: %s\nActually: %s\n' % (
            key, value, b[key])


def mount(obj):
    def decorator(func):
        obj.__dict__[func.__name__] = func

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator


def _get_url(domain, tag):
    return urlparse.urljoin(domain, tag)

#---------------------------------------------------------------
#  测试查询操作 getAccount(.*)
#---------------------------------------------------------------


@formatter
def test_getAccount(server, user):
    '''
    账户：获取账户信息
    '''
    res = getAccount(server=server, header=user, body=GETACCOUNT)
    assert_header(res.header, STATUS.SUCCESS)
    # 这里应该是查询数据库，对比数据

    GLOBAL[TAG_TYPE]['output'] = res.body.accountInfoType


#---------------------------------------------------------------
#  测试更新操作 updateAccount
#---------------------------------------------------------------


def _update_by_dict(server, user, change, expected):
    # 获取修改后的账户的期望结果
    res = getAccount(server=server, header=user, body=GETACCOUNT)
    account = AccountInfoType(**res.body.accountInfoType)
    account.update(expected)
    # 修改账户
    change = AccountInfoType(**change)
    res = updateAccount(server=server, header=user, body=change)
    assert_header(res.header, STATUS.SUCCESS)
    res_after = getAccount(server=server, header=user, body=GETACCOUNT)
    # 对比
    _compare_dict(account, res_after.body.accountInfoType)


@formatter
def test_updateAccount_unchange(server, user):
    '''
    账户：更新操作，不做任何更新
    '''
    change = dict(
        # userId=1234567,
        # userName="hahaha",
        # balance=654321.59,
        # cost=123.39,
        # payment=7779.03,
        budgetType=None,
        budget=None,
        regionTarget=[],
        excludeIp=[],
        # openDomains='http://test.com',
        # regDomain='http://test.com',
        # weeklyBudget=123.79,
    )
    _update_by_dict(server, user, change, {})
    # recovery
    # updateAccount(server=server, header=user, body=account)


@formatter
def test_updateAccount_price_2place(server, user):
    '''
    账户：更新操作，设置账户预算为两位小数，测试精度
    '''
    account = GLOBAL[TAG_TYPE]['output']
    change = dict(budgetType=1, budget=10.59)
    expected = dict(budgetType=1, budget=10.59, weeklyBudget=[10.59])
    _update_by_dict(server, user, change, expected)
    # recovery
    recovery = AccountInfoType(
        budget=account.budget, budgetType=account.budgetType)
    updateAccount(server=server, header=user, body=recovery)


@formatter
def test_updateAccount_clear_price(server, user):
    '''
    账户：更新操作，取消账户预算
    '''
    account = GLOBAL[TAG_TYPE]['output']
    change = dict(budgetType=0)
    expected = dict(budgetType=0, budget=0.0, weeklyBudget=[-1.0])
    _update_by_dict(server, user, change, expected)
    # recovery
    recovery = AccountInfoType(
        budget=account.budget, budgetType=account.budgetType)
    updateAccount(server=server, header=user, body=recovery)


@formatter
def test_updateAccount_clear_regionTarget(server, user):
    '''
    账户：更新操作，取消目标投放地域限制
    '''
    account = GLOBAL[TAG_TYPE]['output']
    recovery = AccountInfoType(regionTarget=[u"北京", u"香港"])
    updateAccount(server=server, header=user, body=recovery)
    change = dict(regionTarget=[u"所有地域"])
    _update_by_dict(server, user, change, change)
    # recovery
    recovery = AccountInfoType(regionTarget=account.regionTarget)
    updateAccount(server=server, header=user, body=recovery)


@formatter
def test_updateAccount_clear_excludeIp(server, user):
    '''
    账户：更新操作，取消目标IP排除限制
    '''
    account = GLOBAL[TAG_TYPE]['output']
    recovery = AccountInfoType(excludeIp=["127.0.0.*", "8.8.*.*"])
    updateAccount(server=server, header=user, body=recovery)
    change = dict(excludeIp=["$"])
    expected = dict(excludeIp=[""])
    _update_by_dict(server, user, change, expected)
    # recovery
    recovery = AccountInfoType(excludeIp=account.excludeIp)
    updateAccount(server=server, header=user, body=recovery)


@mount(api.account)
def test_updateAccount(server, user):
    GLOBAL[TAG_TYPE]['output'] = getAccount(
        server=server, header=user, body=GETACCOUNT).body.accountInfoType

    test_updateAccount_unchange(server, user)
    test_updateAccount_price_2place(server, user)
    test_updateAccount_clear_price(server, user)
    test_updateAccount_clear_regionTarget(server, user)
    test_updateAccount_clear_excludeIp(server, user)


#-------------------------------------------------------------------------
#  测试入口
#-------------------------------------------------------------------------


@mount(api.newCreative)
def test_main(server=SERVER, user=DEFAULT_USER, recover=True):
    user.get_tag(TAG_TYPE, refresh=True)
    results = ThreadLocal.get_results()
    len_before = len(results)

    test_getAccount(server, user)
    test_updateAccount(server, user)
    # test_deleteAccount(server, user)

    flag = all(
        (results[i].status == 'PASS' for i in range(len_before, len(results))))
    # TODO
