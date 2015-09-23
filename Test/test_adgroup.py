# -*- coding:utf-8 -*-
'''
Adgroup Service
Type:
    CampaignAdgroupId:
    {
        "campaignId": long
        "adgroupIds": long[]
    }

'''

import logging
from APITest.settings import api
from APITest.models.adgroup import *
from APITest.utils import assert_header, get_log_filename
from APITest.models.user import UserObject
from APITest.models.const import STATUS
from APITest.compat import (
    ThreadLocal, formatter, gen_chinese_unicode, log_dec)
from APITest.models.adgroup import *
import threading
from itertools import izip
from functools import update_wrapper

##########################################################################
#    log settings

TAG_TYPE = u'ADGROUP'
LOG_FILENAME = get_log_filename(TAG_TYPE)

__loglevel__ = logging.DEBUG
log = logging.getLogger(__name__)
log.setLevel(__loglevel__)

MAX_CAMPIGN_AMOUNT = 500
MAX_ADGROUP_PER_CAMPAIGN = 2000

##########################################################################
SERVER = ThreadLocal.SERVER
USER = ThreadLocal.USER

'''
"adgroup": {
    "getAllAdgroupId": APIRequest(
        method=post, uri='/api/adgroup/getAllAdgroupId'),
    "getAdgroupIdByCampaignId": APIRequest(
        method=post, uri='/api/adgroup/getAdgroupIdByCampaignId'),
    "getAdgroupByCampaignId": APIRequest(
        method=post, uri='/api/adgroup/getAdgroupByCampaignId'),
    "getAdgroupByAdgroupId": APIRequest(
        method=post, uri='/api/adgroup/getAdgroupByAdgroupId'),
    "addAdgroup": APIRequest(
        method=post, uri='/api/adgroup/addAdgroup'),
    "updateAdgroup": APIRequest(
        method=post, uri='/api/adgroup/updateAdgroup'),
    "deleteAdgroup": APIRequest(
        method=delete, uri='/api/adgroup/deleteAdgroup'),
}
'''
locals().update(api.campaign)
locals().update(api.adgroup)

_local_ = threading.local()
GLOBAL = _local_.__dict__.setdefault('global', {})
GLOBAL[TAG_TYPE] = {}
# ------------------------------------------------------------------------
# 定义测试用例 addAdgroup
# ------------------------------------------------------------------------


def _compare_dict(exp, act):
    '''
    @param exp: expected
    @param act: actually
    '''
    log.debug('Compare object:\nExpected: %s\nActually: %s', exp, act)
    for key, value in exp.iteritems():
        if value is None:
            continue
        assert value == act[key], 'Content Differ at key `%s`!\n'\
            'Expected: %s\nActually: %s\n' % (key, value, act[key])


def _get_campaignId(server, user, refresh=False):
    tag = user.get_tag(TAG_TYPE, refresh)
    tag_dict = ThreadLocal.get_tag_dict((server, user.username), tag)
    if 'campaignId' not in tag_dict:
        tag_dict.update(user.add_campaign(server, TAG_TYPE))
    return tag_dict['campaignId']

# ------------------------------------------------------------------------
# 定义测试用例 添加操作
# ------------------------------------------------------------------------


def add_setup(func):
    def wrapper(server, user):
        adgroup = func(server, user)
        adgroup.campaignId = _get_campaignId(server, user)
        log.debug('addAdgroup: %s', adgroup)
        res = user.addAdgroup(server=server, body=adgroup)
        assert_header(res.header, STATUS.SUCCESS)
        adgroupId = res.body.adgroupTypes[0].adgroupId
        # FIXME
        # 这里应该是查询数据库，对比数据
        ret = user.getAdgroupByAdgroupId(
            server=server, body=AdgroupId(adgroupId))
        expected = adgroup.normalize(adgroupId=adgroupId)
        actually = ret.body.adgroupTypes[0]
        _compare_dict(expected, actually)

        # TearDown
        res = deleteAdgroup(
            server=server, header=user,
            body=AdgroupId(adgroupId))
        assert_header(res.header, STATUS.SUCCESS)

    return update_wrapper(wrapper, func)


@formatter
@add_setup
def test_add_default(server, user):
    ''' 单元：添加单元，选填项全部留空 '''
    return AdgroupType.random()


@formatter
@add_setup
def test_add_title30(server, user):
    ''' 单元：添加单元，标题长度为30 '''
    return AdgroupType.random(
        adgroupName=gen_chinese_unicode(30),
    )


@formatter
def test_add_title31(server, user):
    ''' 单元：添加单元，标题长度为31，报错901413 '''
    campaignId = _get_campaignId(server, user)
    adgroup = AdgroupType.random(
        campaignId=campaignId,
        adgroupName=gen_chinese_unicode(31)
    )
    res = user.addAdgroup(server=server, body=adgroup)
    log.debug('Response: %s\n%s', res.content, '- ' * 40)
    assert_header(res.header, STATUS.FAIL, 901413)


@formatter
def test_add_maxPrice01(server, user):
    ''' 单元：添加单元，标价小于0.3，报错901421 '''
    campaignId = _get_campaignId(server, user)
    adgroup = AdgroupType.random(
        campaignId=campaignId,
        maxPrice=0.29999998
    )
    res = user.addAdgroup(server=server, body=adgroup)
    log.debug('Response: %s\n%s', res.content, '- ' * 40)
    assert_header(res.header, STATUS.FAIL, 901421)


@formatter
@add_setup
def test_add_maxPrice00(server, user):
    ''' 单元：添加单元，标价设置为999.99，正常添加 '''
    campaignId = _get_campaignId(server, user)
    adgroup = AdgroupType.random(
        campaignId=campaignId,
        maxPrice=999.9899998
    )
    return adgroup


@formatter
def test_add_maxPrice02(server, user):
    ''' 单元：添加单元，标价大于999.99，报错901422 '''
    campaignId = _get_campaignId(server, user)
    adgroup = AdgroupType.random(
        campaignId=campaignId,
        maxPrice=999.991
    )
    res = user.addAdgroup(server=server, body=adgroup)
    log.debug('Response: %s\n%s', res.content, '- ' * 40)
    assert_header(res.header, STATUS.FAIL, 901422)


@formatter
@add_setup
def test_add_maxPrice03(server, user):
    ''' 单元：添加单元，标价为917.14993，应变成.15 实际是.16 '''
    return AdgroupType.random(maxPrice=917.1499308145)


@formatter
@add_setup
def test_add_pause00(server, user):
    ''' 单元：添加单元，暂停状态为True '''
    return AdgroupType.random(pause=1, maxPrice=10.49)


def test_addAdgroup(server, user):
    test_add_default(server, user)
    test_add_title30(server, user)
    test_add_title31(server, user)
    test_add_maxPrice00(server, user)
    test_add_maxPrice01(server, user)
    test_add_maxPrice02(server, user)
    test_add_maxPrice03(server, user)
    test_add_pause00(server, user)

# ------------------------------------------------------------------------
# 定义测试用例 更新操作
# ------------------------------------------------------------------------


def update_setup(func):
    def wrapper(server, user):
        campaignId = _get_campaignId(server, user)
        adgroup = AdgroupType.factory(
            campaignId=campaignId)
        log.debug('addAdgroup: %s', adgroup)
        res = user.addAdgroup(server=server, body=adgroup)
        adgroupId = res.body.adgroupTypes[0].adgroupId
        assert_header(res.header, STATUS.SUCCESS)

        # UPDATE
        changes = func(server, user)
        changes.adgroupId = adgroupId
        res = user.updateAdgroup(server=server, body=changes)
        log.debug('updateAdgroup: %s', res.content)
        assert_header(res.header)

        # 更新adgroupId, 及其他
        expected = adgroup[0].normalize(changes)
        # FIXME
        # 这里应该是查询数据库，对比数据
        ret = user.getAdgroupByAdgroupId(
            server=server, body=AdgroupId(adgroupId))
        actually = ret.body.adgroupTypes[0]
        _compare_dict(expected, actually)

        # TearDown
        res = deleteAdgroup(
            server=server, header=user,
            body=AdgroupId(adgroupId))
        assert_header(res.header, STATUS.SUCCESS)

    return update_wrapper(wrapper, func)


@formatter
@update_setup
def test_update_default(server, user):
    ''' 单元：更新单元，选填项全部留空 '''
    return AdgroupType()


@formatter
@update_setup
def test_update_title30(server, user):
    ''' 单元：更新单元，标题长度为30 '''
    return AdgroupType(
        adgroupName=gen_chinese_unicode(30),
        maxPrice=0.3
    )


@formatter
def test_update_title31(server, user):
    ''' 单元：更新单元，标题长度为31，报错901413 '''
    """
    这个是报错，不需要做后续检查，怎么破！
    """
    campaignId = _get_campaignId(server, user)
    adgroup = AdgroupType.factory(
        campaignId=campaignId)
    res = user.addAdgroup(server=server, body=adgroup)
    adgroupId = res.body.adgroupTypes[0].adgroupId
    res = user.updateAdgroup(
        server=server,
        body=AdgroupType(
            adgroupId=adgroupId,
            adgroupName=gen_chinese_unicode(31)
        ))
    log.debug('Response: %s\n%s', res.content, '- ' * 40)
    assert_header(res.header, STATUS.FAIL, 901413)
    user.deleteAdgroup(server=server, body=AdgroupId(adgroupId))


@formatter
def test_update_maxPrice01(server, user):
    ''' 单元：更新单元，标价小于0.3，报错901421 '''
    campaignId = _get_campaignId(server, user)
    adgroup = AdgroupType.factory(
        campaignId=campaignId)
    res = user.addAdgroup(server=server, body=adgroup)
    adgroupId = res.body.adgroupTypes[0].adgroupId
    res = user.updateAdgroup(
        server=server,
        body=AdgroupType(
            adgroupId=adgroupId,
            maxPrice=0.29999998,
        ))
    log.debug('Response: %s\n%s', res.content, '- ' * 40)
    assert_header(res.header, STATUS.FAIL, 901421)
    user.deleteAdgroup(server=server, body=AdgroupId(adgroupId))


@formatter
@update_setup
def test_update_maxPrice00(server, user):
    ''' 单元：更新单元，标价设置为999.99，正常添加 '''
    return AdgroupType(maxPrice=999.9899998)


@formatter
def test_update_maxPrice02(server, user):
    ''' 单元：更新单元，标价大于999.99，报错901422 '''
    campaignId = _get_campaignId(server, user)
    adgroup = AdgroupType.factory(
        campaignId=campaignId)
    res = user.addAdgroup(server=server, body=adgroup)
    adgroupId = res.body.adgroupTypes[0].adgroupId
    res = user.updateAdgroup(
        server=server,
        body=AdgroupType(
            adgroupId=adgroupId,
            maxPrice=999.991
        ))
    log.debug('Response: %s\n%s', res.content, '- ' * 40)
    assert_header(res.header, STATUS.FAIL, 901422)


@formatter
@update_setup
def test_update_maxPrice03(server, user):
    ''' 单元：更新单元，标价为917.14993，应变成.15 '''
    return AdgroupType(maxPrice=917.1499308145)


@formatter
@update_setup
def test_update_pause00(server, user):
    ''' 单元：更新单元，暂停状态为True '''
    return AdgroupType(pause=1)


def test_updateAdgroup(server, user):
    test_update_default(server, user)
    test_update_title30(server, user)
    test_update_title31(server, user)
    test_update_maxPrice00(server, user)
    test_update_maxPrice01(server, user)
    test_update_maxPrice02(server, user)
    test_update_maxPrice03(server, user)
    test_update_pause00(server, user)

# ------------------------------------------------------------------------
# 定义测试用例 getAdgroup*
# ------------------------------------------------------------------------


class AdgroupFactory(object):

    def __init__(self, amount=1, tearDown=True):
        self.amount = amount
        self.tearDown = tearDown

    def _setup(self, server, user):
        self.campaignId = campaignId = _get_campaignId(server, user, True)
        amount = self.amount
        self.raw_factory = factory = AdgroupType.factory(campaignId, amount)
        log.debug('Add Adgroup to campaignId: %s', campaignId)
        log.debug('Adgroups: %s\n%s', factory, '- ' * 40)
        self.response = res = user.addAdgroup(
            server=server, body=factory)
        assert_header(res.header, STATUS.SUCCESS)
        ret = res.body.adgroupTypes
        assert len(ret) == amount, '_add_factory: length of adgroups'\
            ' differ: %s != %s' % (len(ret), amount)
        # 返回的是 由低到高 排序的 !
        self.factory = list(x.normalize(adgroupId=y.adgroupId)
                            for x, y in izip(factory, ret))

    def _teardown(self, server, user):
        ''' delete item in self.factory '''
        res = deleteAdgroup(
            server=server, header=user,
            body=AdgroupId(x.adgroupId for x in self.factory))
        assert_header(res.header, STATUS.SUCCESS)

    def __call__(self, func):
        def wrapper(server, user, **kwargs):
            self._setup(server, user)
            kwargs.update(factory=self.factory)
            ret = func(server, user, **kwargs)
            if self.tearDown:
                self._teardown(server, user)
            return ret
        return update_wrapper(wrapper, func)


@formatter
# formatter 放在最外层，否则无法记录setup/teardown失败的用例
@AdgroupFactory(3)
def test_getAdgroupIdByCampaignId(server, user, factory):
    ''' 单元：获取计划ID下的所有单元ID '''
    adgroups = factory
    log.debug('Preparation: %s', adgroups)
    campaignId = adgroups[0].campaignId
    res = getAdgroupIdByCampaignId(
        header=user, server=server,
        body=CampaignId(campaignId))
    assert_header(res.header, STATUS.SUCCESS)
    # FIXME
    # 这里应该是查询数据库，对比数据
    campaignAdgroupIds = res.body.campaignAdgroupIds[0]
    assert campaignAdgroupIds.campaignId == campaignId
    expected = [x.adgroupId for x in adgroups]
    actually = campaignAdgroupIds.adgroupIds
    assert set(expected) == set(actually), 'AdgrupIds Differ!\n'\
        'Expected: %s\nActually: %s' % (expected, actually)


@formatter
@AdgroupFactory(7)
def test_getAdgroupByCampaignId(server, user, factory):
    ''' 单元：获取计划ID下的所有单元的数据 '''
    adgroups = factory
    log.debug('Preparation: %s', adgroups)
    campaignId = adgroups[0].campaignId
    res = getAdgroupByCampaignId(
        header=user, server=server,
        body=CampaignId(campaignId))
    assert_header(res.header, STATUS.SUCCESS)
    # FIXME
    # 这里应该是查询数据库，对比数据
    campaignAdgroups = res.body.campaignAdgroups[0]
    assert campaignAdgroups.campaignId == campaignId
    expected = sorted(adgroups, key=lambda x: x.adgroupId)
    actually = sorted(campaignAdgroups.adgroupTypes, key=lambda x: x.adgroupId)
    for _exp, _act in izip(expected, actually):
        _compare_dict(_exp, _act)


@formatter
@AdgroupFactory(5)
def test_getAdgroupByAdgroupId(server, user, factory):
    ''' 单元：获取单元ID对应的单元数据 '''
    adgroups = factory
    log.debug('Preparation: %s', adgroups)
    ids = [x.adgroupId for x in adgroups]
    res = getAdgroupByAdgroupId(
        header=user, server=server,
        body=AdgroupId(ids))
    assert_header(res.header, STATUS.SUCCESS)
    # Assertion
    expected = sorted(adgroups, key=lambda x: x.adgroupId)
    actually = sorted(res.body.adgroupTypes, key=lambda x: x.adgroupId)
    for _exp, _act in izip(expected, actually):
        _compare_dict(_exp, _act)


def test_getAdgroup(server, user):
    test_getAdgroupIdByCampaignId(server, user)
    test_getAdgroupByAdgroupId(server, user)
    test_getAdgroupByCampaignId(server, user)


# ------------------------------------------------------------------------
# 定义测试用例 getAdgroup*
# ------------------------------------------------------------------------
@formatter
def test_delete00(server, user):
    ''' 单元：删除10个单元 '''
    obj = AdgroupFactory(10)
    obj._setup(server, user)
    ids = set(x.adgroupId for x in obj.factory)
    res = getAdgroupIdByCampaignId(
        header=user, server=server,
        body=CampaignId(obj.campaignId))
    log.debug('getAdgroup: %s', res.content)
    assert ids == set(
        res.body.campaignAdgroupIds[0].adgroupIds), 'Add Adgroup Failed!'
    obj._teardown(server, user)
    res = getAdgroupIdByCampaignId(
        header=user, server=server,
        body=CampaignId(obj.campaignId))
    new_ids = res.body.campaignAdgroupIds[0].adgroupIds
    assert len(new_ids) == 0, 'Delete Failed: %s' % (new_ids)


def test_deleteAdgroup(server, user):
    test_delete00(server, user)

# ------------------------------------------------------------------------
# 测试入口 main()
# ------------------------------------------------------------------------


@log_dec(log, LOG_FILENAME, __loglevel__)
def test_main(server=None, user=None):
    server = server or ThreadLocal.SERVER
    user = user or ThreadLocal.USER
    test_addAdgroup(server, user)
    test_updateAdgroup(server, user)
    test_getAdgroup(server, user)
    test_deleteAdgroup(server, user)
