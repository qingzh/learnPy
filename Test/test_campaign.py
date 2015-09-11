# -*- coding:utf-8 -*-
'''
一个账户最多500个计划
一个计划最多2000个单元
一个账户最多100,000个单元
一个单元最多20,000个单元
一个账户最多2,000,000,000个关键词
一个单元最多50个创意
一个账户最多1,000,000个创意

针对 "计划" Campaign 接口的回归测试
get by id:
get all id:
get all:
add:
update:
delete:

TODO:
  * 测试级联删除  state表
'''
__version__ = 1.0
__author__ = 'Qing Zhang'

import json
import logging
from APITest.models.models import (APIData, AttributeDict)
from APITest.utils import assert_header
from TestCommon.models.const import STDOUT, BLANK
from APITest.models.campaign import *
import random
from APITest import settings
from APITest.settings import SERVER, USERS, api
from APITest.utils import assert_header
from itertools import izip
import threading
import collections
import uuid
from APITest.models.user import UserObject
from APITest.models.const import STATUS
from APITest.compat import formatter
from TestCommon.exceptions import UndefinedException
from TestCommon import ThreadLocal
from datetime import datetime
##########################################################################
#    log settings

TAG_TYPE = u'计划'
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

MAX_CAMPIGN_AMOUNT = 500
DEFAULT_USER = UserObject(**USERS.get('wolongtest'))

'''
"campaign": {
    "getAllCampaignId": APIRequest(method=post, uri='/api/campaign/getAllCampaignID'),
    "getAllCampaign": APIRequest(method=post, uri='/api/campaign/getAllCampaign'),
    "getCampaignByCampaignId": APIRequest(method=post, uri='/api/campaign/getCampaignByCampaignId'),
    "updateCampaign": APIRequest(method=post, uri='/api/campaign/updateCampaign'),
    "deleteCampaign": APIRequest(method=delete, uri='/api/campaign/deleteCampaign'),
    "addCampaign": APIRequest(method=post, uri='/api/campaign/addCampaign')
}
'''
locals().update(api.campaign)

#-------------------------------------------------------------------------
# 准备测试数据
# description 总长
# 字典里存的是json形式，因为list不能hash
#-------------------------------------------------------------------------

campaign_map = AttributeDict(
    budget={
        # value_in_request:value_in_response
        '0': '-1'  # be care of numeric & string
    },
    regionTarget={
        '["所有地域"]': '["所有地域"]'
    },
    excludeIp={
        '["$"]': '[""]'
    },
    negativeWords={
        '["$"]': '[""]'
    },
    exactNegativeWords={
        '["$"]': '[""]'
    },
    schedule={
        '[{"weekDay":0}]': json.dumps([
            {"endHour": 24, "weekDay": 1, "startHour": 0},
            {"endHour": 24, "weekDay": 2, "startHour": 0},
            {"endHour": 24, "weekDay": 3, "startHour": 0},
            {"endHour": 24, "weekDay": 4, "startHour": 0},
            {"endHour": 24, "weekDay": 5, "startHour": 0},
            {"endHour": 24, "weekDay": 6, "startHour": 0},
            {"endHour": 24, "weekDay": 7, "startHour": 0}])
    },
    showProb={

    },
    pause={

    }
)

#-------------------------------------------------------------------------


def parse_update_map(update_map):
    '''
    @param update_map: dict{
        key:{
            old_value: new_value
        }
    }
    @return set_list, new_list
    '''
    set_list, new_list = [], []
    for key, value_map in update_map.iteritems():
        for set_value, new_value in value_map.iteritems():
            set_list.append({key: json.loads(set_value)})
            new_list.append({key: json.loads(new_value)})
    return set_list, new_list


def doRequest(req, body={}, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    req.response(**kwargs)
    @return requests.Response
    '''
    data = APIData(header=user)
    data.body = AttributeDict(body)
    res = req.response(server, json=data)
    log.debug(res.request.url)
    log.debug('[REQUEST ] %s' % res.request.body)
    log.debug('[RESPONSE] %s' % res.content)
    return res


def _update(body):
    if not isinstance(body, collections.Sequence):
        body = [body]
    return doRequest(updateCampaign, {"campaignTypes": body})


def test_updateCampaign():
    '''
    POST /cpc/campaign/updateCampaign

    可以更新的域：
    campaignId  必填
    campaignName: 15个汉字或者30个英文
        选填 默认为NULL: 不修改该属性
        如果填写campaignName,更改名称必须与原计划名称不同，否则会报错
    budget
        选填 默认为NULL: 不修改该属性
        0：取消计划预算限制
    regionTarget
        选填 默认为NULL:不修改该属性
        填写”所有地域”：取消投放地域限制
    excludeIp
        选填 默认为NULL:不修改该属性
        值为$(数组仅1个元素, 值为$)：取消IP排除
    negativeWords
        选填 默认为NULL :不修改该属性
        值为$(数组仅1个元素, 值为$)：取消否定词
    exactNegativeWords
        选填 默认为NULL :不修改该属性
        值为$(数组仅1个元素, 值为$)：取消精确否定词
    schedule
        选填 默认为NULL :不修改该属性
        数组仅1个元素, 且该元素的weekDay为0：取消暂停时段
    budgetOfflineTime
        无效,返回为null
    showProb
        选填 默认为NULL :不修改该属性
    pause
        选填 默认为NULL :不修改该属性
    status
        无效属性
    '''
    # Negative Cases:
    test_update_with_existing_name()

    # Positive Cases
    test_update_with_duplicate_campaigns()
    test_update_using_map(campaign_map)


# @suite(SUITE.API)  # 动态分配测试集合


@formatter
def test_update_with_existing_name():
    ''' 使用已存在的计划名称更新计划，预期结果："计划名称已存在" '''
    '''
    计划名称重复
    1. 和当前计划的名字相同 ?? 我认为这是可以接受的……
    2. 和该账户其他计划的名字相同
    3. 和其他账户的计划名字相同
    '''
    data = _get_n(1).body.campaignTypes[0]
    # FAILURE case: update with same campaignName
    res = _update(data)
    assert_header(res.header, 2)
    assert {"code": 901203,
            "message": u"计划名称已存在"} in res.header.failures, res.header

    data_list = _get_n(2).body.campaignTypes
    data_list[0].campaignName = data_list[1].campaignName
    res = _update(data_list[0:1])
    # assert res.status_code == 404
    assert_header(res.header, 2)
    assert {"code": 901203,
            "message": u"计划名称已存在"} in res.header.failures, res.header


@formatter
def test_update_with_duplicate_campaigns():
    '''
    测试更新列表中存在重复的计划id，预期结果：以最后的更新值为准
    '''
    data = _get_n(1).body.campaignTypes[0]
    _list = list(yield_campaignType(3))
    map(lambda x: x.update(campaignId=data.campaignId), _list)
    res = _update(_list)
    new_data = _get_by_ids(data.campaignId).body.campaignTypes[0]
    assert new_data >= _list[-1]


@formatter
def test_update_using_map(campaign_map):
    '''
    依次更新计划的属性，预期结果：全部更新成功
    '''

    _delete_all()
    set_list, new_list = parse_update_map(campaign_map)
    update_list = _get_n(len(set_list)).body.campaignTypes
    # REMOVE campaignName to get rid of `901203` error
    # 删除 campaignName，否则 相同的campaignName会引发异常
    for item, _set in izip(update_list, set_list):
        item.update(_set)
        item.pop('campaignName')

    res = _update(update_list)
    assert_header(res.header, 0)
    update_bd = res.body.campaignTypes
    assert update_bd <= update_list

    res = _get_by_ids([x.campaignId for x in update_list])
    assert_header(res.header, 0)
    after = res.body.campaignTypes
    for item, _new in izip(after, new_list):
        assert item >= _new, 'EXPECTED:\n%sEXACTED:\n%s' % (item, _new)


def _subset(_set, k=None):
    '''
    Choose k items from a sequence
    @param _set: super set, should have at least 2 items
    @param k: should be not larger than len(_set)
    '''
    k = k or random.randrange(1, len(_set))
    return random.sample(_set, k)


def _shuffle(_list):
    random.shuffle(_list)
    return _list


@formatter
def test_delete_subset(server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    删除部分现存计划，不含不存在的计划
    '''
    all_before = _get_nlt_n_ids(10)
    # get subset of existing ids
    del_ids = _subset(all_before.body.campaignIds)
    del_bd = _delete_list(del_ids)
    assert_header(del_bd.header, 0)
    all_after = _get_all_ids(server, user, recover)
    assert set(all_before.body.campaignIds).difference(
        set(all_after.body.campaignIds)) == set(del_ids), '%s\n%s\n%s' % (all_before, del_ids, all_after)


@formatter
def test_delete_cross_user():
    '''
    删除其他用户的计划，暂未实现
    '''
    raise UndefinedException


@formatter
def test_delete_mixed(server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    删除部分现存计划，包含不存在的计划ID
    预期结果：存在的计划ID成功删除，不存在的计划ID返回
    '''
    ids_before = _get_nlt_n_ids(10).body.campaignIds
    min_id = min(ids_before)
    del_ids = _subset(ids_before)
    err_ids = _subset(range(min_id - len(ids_before), min_id))
    del_bd = _delete_list(_shuffle(del_ids + err_ids))
    assert_header(del_bd.header, 1)
    all_set = set(_get_all_ids().body.campaignIds)
    assert all_set.isdisjoint(
        del_ids + err_ids), 'Partial delettion case failed!\n%s should be deleted!' % all_set.intersection(del_ids + err_ids)
    assert set(del_bd.body.campaignIds) == set(
        err_ids), 'Partial deletion case failed!\nExpected failed id: %s\nExact failed id: %s' % (err_ids, del_bd.body.campaignIds)


#@formatter
def test_delete_all(params={}, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    删除账户的所有计划
    '''
    all_before = _get_nlt_n_ids(10)
    del_bd = _delete_list(all_before.body.campaignIds)
    all_after = _get_all_ids()
    assert_header(del_bd.header, 0)
    assert del_bd.body <= dict(result=0, campaignIds=[])
    assert all_after.body == dict(
        campaignIds=[]), 'Content Differ!\nExpected: EMPTY\nActually: %s\n' % (all_after.body)


def test_deleteCampaign():
    test_delete_subset()
    test_delete_mixed()
    test_delete_all()


def _get_nlt_n_ids(n, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    get not less than `n` ids
    @return : list of campaign ids
    为账户准备至少 n 个计划
    如果已经存在超过(或等于)n个计划，则直接返回
    否则添加至 n 个计划
    '''
    get_bd = _get_all_ids()
    if n <= len(get_bd.body.campaignIds):
        return get_bd
    bd = _add_n(n - len(get_bd.body.campaignIds))
    _bd = json.loads(bd.request.body, object_hook=AttributeDict)
    assert_header(bd.header, 0)
    assert _bd.body <= bd.body
    return _get_all_ids()


def _get_all_ids(server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    get all campaignIds
    this request should be always `success` except network issues
    @return object like {'campaignIds':[...]}
    '''
    res = doRequest(getAllCampaignId, {}, server, user, recover)
    # assert res.status_code == 200
    assert_header(res.header, 0)
    return res


def _get_by_ids(ids, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    @return: requests.Response object
    '''
    if not isinstance(ids, collections.Sequence):
        ids = [ids]
    return doRequest(getCampaignByCampaignId, {'campaignIds': ids})


def _get_n(n, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    get `n` campaigns by random
    @return : list of campaigns
    为账户准备至少 n 个计划
    如果已经存在超过(或等于)n个计划，则随机返回n个计划
    否则添加至 n 个计划
    '''
    bd = _get_nlt_n_ids(n, server, user, recover)
    return _get_by_ids(_subset(bd.body.campaignIds, n))


def _get_all(server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    get all campaigns
    '''
    res = doRequest(getAllCampaign, {}, server, user, recover)
    # assert res.status_code == 200
    assert_header(res.header, 0)
    return res


def _add_n(n, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    添加 n 个计划，不管成功与否，意即不做任何assertion
    输入：n
    返回：Response Object
    '''
    if n <= 0:
        return
    campaigns = list(yield_campaignType(n))
    res = _add_list(campaigns, server, user, recover)
    return res


def _add_list(campaign_list, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    添加 campaigns; 如果超过500个则全部失败
    @param campaign_list: list of new campaigns
    '''
    res = doRequest(addCampaign, body={'campaignTypes': campaign_list})
    return res


def test_addCampaign():
    # SUCCESS cases
    test_add_n(1)
    test_add_n(random.randrange(2, MAX_CAMPIGN_AMOUNT))
    test_add_n(MAX_CAMPIGN_AMOUNT)
    # FAILURE cases
    test_add_exceed(MAX_CAMPIGN_AMOUNT)
    test_add_duplicate()
    # TODO: 目前添加的计划里只要包含1个重复case就是失败的
    test_add_mixed()


@formatter
def test_add_duplicate():
    '''
    新增的计划名称已存在，期望返回：报错
    '''
    _delete_all()
    bd = _get_n(1)
    res = _add_list(bd.body.campaignTypes)
    assert_header(res.header, 2)
    assert {"code": 901203,
            "message": u"计划名称已存在"} in res.header.failures, res.header


@formatter
def test_add_mixed():
    '''
    批量插入，部分计划名称已存在
    '''
    # TODO 可能计划数满了，意即 inexistence < 1
    _delete_all()
    ids = _get_nlt_n_ids(10).body.campaignIds
    existing = _get_by_ids(_subset(ids)).body.campaignTypes
    inexistence = list(yield_campaignType(10))
    res = _add_list(_shuffle(existing + inexistence))
    # assert res.status_code == 404
    assert_header(res.header, 2)
    assert {"code": 901203,
            "message": u"计划名称已存在"} in res.header.failures, res.header


@formatter
def test_add_n(n, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    测试添加n个计划，不包括总数溢出
    '''
    # Clean Up
    _delete_all()
    data = list(yield_campaignType(n))
    add_bd = _add_list(data)
    assert_header(add_bd.header, STATUS.SUCCESS)
    # Compare items in order:
    # TODO: sort if return list not in order
    for req_bd, res_bd in izip(data, add_bd.body.campaignTypes):
        assert res_bd >= req_bd
    all_campaigns = _get_all()
    func = lambda y: sorted(y.body.campaignTypes, key=lambda x: x.campaignId)
    for add_value, get_value in izip(func(add_bd), func(all_campaigns)):
        assert add_value <= get_value


@formatter
def test_add_exceed(maxn=MAX_CAMPIGN_AMOUNT, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    测试添加计划后，计划总数超过500
    '''
    all_before = _get_all_ids()
    n = random.randint(maxn, maxn << 1)
    res = _add_n(n)
    assert_header(res.header, 2)
    assert {
        "code": 901204, "message": u"推广计划数量不能超过500个"} in res.header.failures, res.body
    all_after = _get_all_ids()
    assert all_before.body == all_after.body, '[BEFORE]: %s\n[AFTER]: %s\n' % (
        all_before.body, all_after.body)


def _delete_all(server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    删除所有计划
    body.result: 0 全部成功，1 部分失败，2 全部失败
    '''
    bd = _get_all_ids(server, user, recover)
    if bd.body.campaignIds:
        del_bd = _delete_list(
            bd.body.campaignIds, server, user, recover)
        assert 0 == del_bd.body.result, 'Delete all campaigns failed!\n%s' % del_bd.body.campaignIds


def _delete_list(_list, server=SERVER, user=DEFAULT_USER, recover=False):
    if not isinstance(_list, collections.Sequence):
        _list = [_list]
    res = doRequest(
        deleteCampaign, {'campaignIds': _list}, server, user, recover)
    return res


def test_campaign_main():
    test_updateCampaign()
    test_deleteCampaign()
    test_addCampaign()
