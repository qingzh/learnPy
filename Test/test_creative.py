# -*- coding:utf-8 -*-
'''
针对 附加创意 (NewCreative) 接口的回归测试:
'''
__version__ = 1.0
__author__ = 'Qing Zhang'

from APITest.model.models import (APIData, AttributeDict)
from TestCommon.models.const import STDOUT, BLANK
from APITest.model.keyword import *
from APITest.settings import USERS, api, LOG_DIR
from APITest import settings
from APITest.utils import assert_header
import collections
from TestCommon.utils import formatter
from APITest.model import image
from APITest.model.user import UserObject
from APITest.model.const import STATUS
from TestCommon import ThreadLocal
from TestCommon.exceptions import UndefinedException
import threading
from datetime import datetime
import logging
from TestCommon.utils import gen_chinese_unicode
##########################################################################
#    log settings

TAG_TYPE = u'创意'
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

SERVER = settings.SERVER.BETA
DEFAULT_USER = UserObject(**USERS.get('ShenmaPM2.5'))


'''
"creative": {
    "getCreativeIdByAdgroupId": APIRequest(method=post, uri='/api/creative/getCreativeIdByAdgroupId'),
    "getCreativeByAdgroupId": APIRequest(method=post, uri='/api/creative/getCreativeByAdgroupId'),
    "getCreativeByCreativeId": APIRequest(method=post, uri='/api/creative/getCreativeByCreativeId'),
    "getCreativeStatus": APIRequest(method=post, uri='/api/creative/getCreativeStatus'),
    "addCreative": APIRequest(method=post, uri='/api/creative/addCreative'),
    "updateCreative": APIRequest(method=post, uri='/api/creative/updateCreative'),
    "deleteCreative": APIRequest(method=delete, uri='/api/creative/deleteCreative'),
    # 区别于activate keywords
    "activeCreative": APIRequest(method=post, uri='/api/creative/activeCreative'),
}
'''
locals().update(api.creative)

#-------------------------------------------------------------------------
# 准备测试数据
# description 总长
# 字典里存的是json形式，因为list不能hash
#-------------------------------------------------------------------------

_local_ = threading.local()
GLOBAL = _local_.__dict__.setdefault('global', {})
GLOBAL[TAG_TYPE] = {}

#-------------------------------------------------------------------------


@formatter
def test_update_same_appId():
    '''
    更新列表包含2个相同的appId，应该以最后更新的为准
    '''
    raise UndefinedException


@formatter
def test_addApp_with_same_adgroupId(server, user):
    '''
    测试给同一个adgroup添加2个app，期望返回：
    '''
    raise UndefinedException


def _getAppIdByAdgroupId(adgroupId, server, user):
    if not isinstance(adgroupId, collections.Sequence):
        adgroupId = [adgroupId]
    res = getAppIdByAdgroupId(
        json=APIData(header=user, body={"adgroupIds": adgroupId}), server=server)
    return res.body


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
#---------------------------------------------------------------
#  添加操作
#  正常添加
#  格式不正确
#---------------------------------------------------------------


def _get_sublink_by_adgroupId(adgroupIds, server, user):
    if not isinstance(adgroupIds, collections.Sequence):
        adgroupIds = [adgroupIds]
    res = doRequest(getSublinkIdByAdgroupId, body={
                    "adgroupIds": adgroupIds}, server=server, user=user)
    return res.body


def _get_adgroupId(server, user, refresh=False):
    tag = user.get_tag(TAG_TYPE, refresh)
    tag_dict = ThreadLocal.get_tag_dict((server, user.username), tag)
    if 'adgroupId' not in tag_dict:
        tag_dict.update(user.add_adgroup(server, TAG_TYPE))
    return tag_dict['adgroupId']


def _delete_adgroupId(server, user):
    tag = user.get_tag(TAG_TYPE)
    tag_dict = ThreadLocal.get_tag_dict((server, user.username), tag)
    user.delete_campaign(server, tag_dict['campaignId'])
    tag_dict.clear()


import urlparse


def _get_url(domain, tag):
    return urlparse.urljoin(domain, tag)


def _get_hostname(domain):
    return urlparse.urlparse(domain).hostname


@formatter
def test_addCreative(server, user):
    '''
    关键词：添加操作(使用默认值)，预期结果：添加成功
    '''
    # 输入物料
    tag = user.get_tag(TAG_TYPE)
    domain = user.domain(server)
    creative = CreativeType(
        creativeId=None,
        adgroupId=_get_adgroupId(server, user),
        title=gen_chinese_unicode(50),
        description1=gen_chinese_unicode(120),
        destinationUrl=_get_hostname(domain),
        displayUrl=_get_url(domain, tag),
        pause=True,
        status=None,
    )
    GLOBAL[TAG_TYPE]['input'] = creative
    res = addCreative(
        server=server, header=user, body=creative)
    assert_header(res.header, STATUS.SUCCESS)
    # 这里应该是查询数据库，对比数据

    creative.creativeId = res.body.creativeTypes[0].creativeId
    GLOBAL[TAG_TYPE]['creativeId'] = creative.creativeId


#---------------------------------------------------------------
#  测试查询操作 getKeyword(.*)
#---------------------------------------------------------------

@formatter
def test_getCreativeId(server, user):
    '''
    创意：获取单元ID下的创意ID getCreativeIdByAdgroupId
    '''
    res = getCreativeIdByAdgroupId(
        header=user, body={'adgroupIds': [_get_adgroupId(server, user)]}, server=server)
    assert_header(res.header, STATUS.SUCCESS)
    assert set(res.body.groupCreativeIds[0].creativeIds) == set(
        [GLOBAL[TAG_TYPE]['creativeId']])


@formatter
def test_getCreativeByAdgroupId(server, user):
    '''
    创意：获取单元ID下的所有创意对象 getCreativeByAdgroupId
    '''
    res = getCreativeByAdgroupId(
        header=user, server=server, body={'adgroupIds': [GLOBAL[TAG_TYPE]['input']['adgroupId']]})
    assert_header(res.header, STATUS.SUCCESS)
    creative = res.body.groupCreatives[0].creativeTypes[0]
    _compare_dict(GLOBAL[TAG_TYPE]['input'], creative)


#@formatter
def test_getCreativeByCreativeId(server, user):
    '''
    创意：获取单元ID下的所有创意对象 getCreativeByCreativeId
    '''
    res = getCreativeByCreativeId(
        header=user, server=server, body={'creativeIds': [GLOBAL[TAG_TYPE]['creativeId']]})
    assert_header(res.header, STATUS.SUCCESS)
    _compare_dict(GLOBAL[TAG_TYPE]['input'], res.body.creativeTypes[0])


#---------------------------------------------------------------
#  测试 getCreativeStatus
#---------------------------------------------------------------


@formatter
def test_getCreativeStatus(server, user):
    '''
    测试了 4 种获取关键词状态方法
    按全账户获取，按计划获取，按单元获取，按关键词ID获取
    '''
    accountId = GroupId(
        ids=None,
        type=None,  # 3表示计划ID，5为单元id，7为关键词id
    )
    res_by_account = getCreativeStatus(
        header=user, server=server, body=accountId)
    assert_header(res_by_account.header, STATUS.SUCCESS)
    res_by_account.body.creativeStatus.sort(key=lambda x: x.id)

    campaignId = GroupId(
        ids=user.get_campaignIds(server),
        type=IDTYPE.CAMPAIGN
    )
    res_by_campaign = getCreativeStatus(
        header=user, server=server, body=campaignId)
    assert_header(res_by_campaign.header, STATUS.SUCCESS)
    res_by_campaign.body.creativeStatus.sort(key=lambda x: x.id)

    def assert_func(x, y, key):
        assert x.body == y.body, 'CreativeStatus by %s differ!\n%s\n%s\n' % (
            key, x.body, y.body)

    assert_func(res_by_account, res_by_campaign, 'campaignIds')

    adgroupId = GroupId(
        ids=user.get_adgroupIds(server),
        type=IDTYPE.ADGROUP
    )
    res_by_adgroup = getCreativeStatus(
        header=user, server=server, body=adgroupId)
    assert_header(res_by_adgroup.header, STATUS.SUCCESS)
    res_by_adgroup.body.creativeStatus.sort(key=lambda x: x.id)
    assert_func(res_by_account, res_by_adgroup, 'adgroupIds')

    creativeId = GroupId(
        ids=user.get_creativeIds(server),
        type=IDTYPE.KEYWORD
    )
    res_by_creative = getCreativeStatus(
        header=user, server=server, body=creativeId)
    assert_header(res_by_creative.header, STATUS.SUCCESS)
    res_by_creative.body.creativeStatus.sort(key=lambda x: x.id)
    assert_func(res_by_account, res_by_creative, 'creativeIds')


@mount(api.creative)
def test_getCreative(server, user):
    test_getCreativeId(server, user)
    test_getCreativeByAdgroupId(server, user)
    test_getCreativeByCreativeId(server, user)

    test_getCreativeStatus(server, user)
    test_getCreative10Quality(server, user)

#---------------------------------------------------------------
#  测试更新操作 updateCreative
#  和 关键词更新很不一样！
#---------------------------------------------------------------


def _updateKeyword_by_dict(server, user, keywordId, change, expected):
    # 获取修改后的关键词的期望结果
    res = getKeywordByKeywordId(
        header=user, server=server, body={'keywordIds': [keywordId]})
    keyword = KeywordType(**res.body.keywordTypes[0])
    keyword.update(expected)
    # 修改关键词
    change = KeywordType(**change)
    change.update(keywordId=keywordId)
    res = updateKeyword(server=server, header=user, body=change)
    assert_header(res.header, STATUS.SUCCESS)
    res_after = getKeywordByKeywordId(
        header=user, server=server, body={'keywordIds': [keywordId]})
    # 对比
    _compare_dict(keyword, res_after.body.keywordTypes[0])


@formatter
def test_updateKeyword_unchange(server, user):
    '''
    关键词：更新操作，不做任何更新
    '''
    keyword = GLOBAL[TAG_TYPE]['output']
    change = dict(
        adgroupId=123456,
        keyword=gen_chinese_unicode(60),
        price=None,
        destinationUrl=None,
        matchType=None,
        pause=None,
        status=123,
    )
    _updateKeyword_by_dict(
        server, user, keyword.keywordId, change, {})
    # recovery
    updateKeyword(server=server, header=user, body=keyword)


@formatter
def test_updateKeyword_clear_price(server, user):
    '''
    关键词：更新操作，取消关键词出价
    '''
    keyword = GLOBAL[TAG_TYPE]['output']
    change = dict(price=0)
    expected = dict(
        price=api.adgroup.getAdgroupByAdgroupId(
            server=server, header=user, body={
                "adgroupIds": [keyword.adgroupId]}
        ).body.adgroupTypes[0].maxPrice
    )
    _updateKeyword_by_dict(
        server, user, keyword.keywordId, change, expected)
    # recovery
    updateKeyword(server=server, header=user, body=keyword)


@formatter
def test_updateKeyword_clear_destinationUrl(server, user):
    '''
    关键词：更新操作，取消目标URL
    '''
    keyword = GLOBAL[TAG_TYPE]['output']
    change = dict(destinationUrl="$")
    expected = dict(destinationUrl="")
    _updateKeyword_by_dict(
        server, user, keyword.keywordId, change, expected)
    # recovery
    updateKeyword(server=server, header=user, body=keyword)


@formatter
def test_activeKeyword(server, user):
    '''
    激活关键词 activateKeyword
    '''
    keyword = GLOBAL[TAG_TYPE]['output']
    change = {'pause': True}
    _updateKeyword_by_dict(server, user, keyword.keywordId, change, change)
    res = activateKeyword(
        header=user, server=server, body={"keywordIds": [keyword.keywordId]})
    assert res.body.keywordTypes[
        0].pause == False, 'Activate keyword failed at `%d`!' % keywordId
    # recovery
    updateKeyword(server=server, header=user, body=keyword)


@mount(api.keyword)
def test_updateKeyword(server, user):
    GLOBAL[TAG_TYPE]['output'] = getKeywordByKeywordId(
        header=user, server=server, body={'keywordIds': [GLOBAL[TAG_TYPE]['keywordId']]}).body.keywordTypes[0]

    test_updateKeyword_unchange(server, user)
    test_updateKeyword_clear_price(server, user)
    test_updateKeyword_clear_destinationUrl(server, user)
    test_activeKeyword(server, user)


#-------------------------------------------------------------------------
#  测试删除操作 deleteKeyword
#-------------------------------------------------------------------------


@formatter
def test_deleteSublink(server, user):
    '''
    推广电话：删除操作 deleteSublink
    '''
    res = deleteSublink(
        header=user, server=server, body={'sublinkIds': [GLOBAL['sublink']['sublinkId']], "newCreativeType": TYPE.SUBLINK})
    assert_header(res.header, STATUS.SUCCESS)
    res = getSublinkIdByAdgroupId(
        header=user, server=server, body={"adgroupIds": [_get_adgroupId(server, user)]})
    ids = res.body.groupSublinkIds[0].sublinkIds
    assert [] == ids, 'Delete sublinkId failed!\n%s remain existing.\n' % (ids)

#-------------------------------------------------------------------------
#  测试入口
#-------------------------------------------------------------------------


@mount(api.newCreative)
def test_main(server=SERVER, user=DEFAULT_USER, recover=True):
    user.get_tag(TAG_TYPE, refresh=True)
    results = ThreadLocal.get_results()
    len_before = len(results)

    test_addKeyword(server, user)
    test_getKeyword(server, user)
    test_updateKeyword(server, user)
    # test_deleteKeyword(server, user)

    flag = all(
        (results[i].status == 'PASS' for i in range(len_before, len(results))))
    flag and recover and _delete_adgroupId(server, user)
