# -*- coding:utf-8 -*-
'''
针对 附加创意 (NewCreative) 接口的回归测试:
'''
from APITest.models.models import (APIData, AttributeDict)
from TestCommon.models.const import BLANK
from APITest.compat import formatter, mount
from APITest.models.keyword import *
from APITest.settings import SERVER, USERS, api
from APITest.utils import assert_header, get_log_filename
import collections
from APITest.models.user import UserObject
from APITest.models.const import STATUS
from APITest.compat import ThreadLocal
from TestCommon.exceptions import UndefinedException
import threading
import logging
from TestCommon.utils import gen_chinese_unicode
import urlparse
##########################################################################
#    log settings

TAG_TYPE = u'关键词'
LOG_FILENAME = get_log_filename(TAG_TYPE)

__loglevel__ = logging.INFO
log = logging.getLogger(__name__)
log.setLevel(__loglevel__)
output_file = logging.FileHandler(LOG_FILENAME, 'w')
output_file.setLevel(__loglevel__)
log.addHandler(output_file)

##########################################################################

DEFAULT_USER = UserObject(**USERS.get('wolongtest'))

'''
"keyword": {
    "getKeywordIdByAdgroupId": APIRequest(
        method=post, uri='/api/keyword/getKeywordIdByAdgroupId'),
    "getKeywordByAdgroupId": APIRequest(
        method=post, uri='/api/keyword/getKeywordByAdgroupId'),
    "getKeywordByKeywordId": APIRequest(
        method=post, uri='/api/keyword/getKeywordByKeywordId'),
    "getKeywordStatus": APIRequest(
        method=post, uri='/api/keyword/getKeywordStatus'),
    "getKeyword10Quality": APIRequest(
        method=post, uri='/api/keyword/getKeyword10Quality'),
    "addKeyword": APIRequest(
        method=post, uri='/api/keyword/addKeyword'),
    "updateKeyword": APIRequest(
        method=post, uri='/api/keyword/updateKeyword'),
    "deleteKeyword": APIRequest(
        method=delete, uri='/api/keyword/deleteKeyword'),
    "activateKeyword": APIRequest(
        method=post, uri='/api/keyword/activateKeyword'),
}
'''
locals().update(api.keyword)

# ------------------------------------------------------------------------
# 准备测试数据
# description 总长
# 字典里存的是json形式，因为list不能hash
# ------------------------------------------------------------------------

_local_ = threading.local()
GLOBAL = _local_.__dict__.setdefault('global', {})
GLOBAL[TAG_TYPE] = {}

# ------------------------------------------------------------------------


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
        json=APIData(header=user,
                     body={"adgroupIds": adgroupId}), server=server)
    return res.body


def _compare_dict(a, b):
    for key, value in a.iteritems():
        if value is None:
            continue
        assert value == b[key], 'Content Differ at key `%s`!\n'\
            'Expected: %s\nActually: %s\n' % (key, value, b[key])
# --------------------------------------------------------------
#  添加操作
#  正常添加
#  格式不正确
# --------------------------------------------------------------


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


def _get_url(domain, tag):
    return urlparse.urljoin(domain, tag)


@formatter
def test_addKeyword(server, user):
    '''
    关键词：添加操作(使用默认值)，预期结果：添加成功
    '''
    # 输入物料
    tag = user.get_tag(TAG_TYPE)
    keyword = KeywordType(
        keywordId=None,
        adgroupId=_get_adgroupId(server, user),
        keyword=gen_chinese_unicode(40),
        price=0.39,
        destinationUrl=_get_url(user.domain(server), tag),
        matchType=1,
        pause=True,
        status=None,
    )
    GLOBAL[TAG_TYPE]['input'] = keyword
    res = addKeyword(
        server=server, header=user, body=keyword)
    assert_header(res.header, STATUS.SUCCESS)
    # 这里应该是查询数据库，对比数据
    keyword.keywordId = res.body.keywordTypes[0].keywordId
    GLOBAL[TAG_TYPE]['keywordId'] = keyword.keywordId


# --------------------------------------------------------------
#  测试查询操作 getKeyword(.*)
# --------------------------------------------------------------

@formatter
def test_getKeywordId(server, user):
    '''
    关键词：获取单元ID下的关键词ID getKeywordIdByAdgroupId
    '''
    res = getKeywordIdByAdgroupId(
        server=server, header=user,
        body={'adgroupIds': [_get_adgroupId(server, user)]})

    assert_header(res.header, STATUS.SUCCESS)
    id_set = set(res.body.groupKeywordIds[0].keywordIds)
    assert id_set >= set([GLOBAL[TAG_TYPE]['keywordId']]), \
        'Expected: %s\nActually:%s\n' % (
        [GLOBAL[TAG_TYPE]['keywordId']], id_set)


@formatter
def test_getKeywordByAdgroupId(server, user):
    '''
    关键词：获取单元ID下的所有关键词对象 getKeywordByAdgroupId
    '''
    res = getKeywordByAdgroupId(
        header=user, server=server,
        body={'adgroupIds': [GLOBAL[TAG_TYPE]['input']['adgroupId']]})
    assert_header(res.header, STATUS.SUCCESS)
    keyword = res.body.groupKeywords[0].keywordTypes[0]
    _compare_dict(GLOBAL[TAG_TYPE]['input'], keyword)


@formatter
def test_getKeywordByKeywordId(server, user):
    '''
    关键词：通过关键词ID获取关键词对象 getKeywordByKeywordId
    '''
    res = getKeywordByKeywordId(
        header=user, server=server,
        body={'keywordIds': [GLOBAL[TAG_TYPE]['keywordId']]})
    assert_header(res.header, STATUS.SUCCESS)
    _compare_dict(GLOBAL[TAG_TYPE]['input'], res.body.keywordTypes[0])


# --------------------------------------------------------------
#  测试 getKeywordStatus
# --------------------------------------------------------------


@formatter
def test_getKeywordStatus(server, user):
    '''
    测试了 4 种获取关键词状态方法
    按全账户获取，按计划获取，按单元获取，按关键词ID获取
    '''
    accountId = GroupId(
        ids=None,
        type=None,  # 3表示计划ID，5为单元id，7为关键词id
    )
    res_by_account = getKeywordStatus(
        header=user, server=server, body=accountId)
    assert_header(res_by_account.header, STATUS.SUCCESS)
    res_by_account.body.keywordStatus.sort(key=lambda x: x.id)

    campaignId = GroupId(
        ids=user.get_campaignIds(server),
        type=IDTYPE.CAMPAIGN
    )
    res_by_campaign = getKeywordStatus(
        header=user, server=server, body=campaignId)
    assert_header(res_by_campaign.header, STATUS.SUCCESS)
    res_by_campaign.body.keywordStatus.sort(key=lambda x: x.id)

    def assert_func(x, y, key):
        assert x.body == y.body, 'KeywordStatus by %s differ!\n'\
            'Request Body: %s\n%s\n%s\n' % (
                key, y.request.body, x.body, y.body)

    assert_func(res_by_account, res_by_campaign, 'campaignIds')

    adgroupId = GroupId(
        ids=user.get_adgroupIds(server),
        type=IDTYPE.ADGROUP
    )
    res_by_adgroup = getKeywordStatus(
        header=user, server=server, body=adgroupId)
    assert_header(res_by_adgroup.header, STATUS.SUCCESS)
    res_by_adgroup.body.keywordStatus.sort(key=lambda x: x.id)
    assert_func(res_by_account, res_by_adgroup, 'adgroupIds')

    keywordId = GroupId(
        ids=user.get_keywordIds(server),
        type=IDTYPE.KEYWORD
    )
    res_by_keyword = getKeywordStatus(
        header=user, server=server, body=keywordId)
    assert_header(res_by_keyword.header, STATUS.SUCCESS)
    res_by_keyword.body.keywordStatus.sort(key=lambda x: x.id)
    assert_func(res_by_account, res_by_keyword, 'keywordIds')


# --------------------------------------------------------------
#  测试 getKeyword10Quality
# --------------------------------------------------------------


@formatter
def test_getKeyword10Quality(server, user):
    '''
    测试了 4 种获取关键词质量度方法
    按全账户获取，按计划获取，按单元获取，按关键词ID获取
    '''
    accountId = GroupId(
        ids=None,
        type=None,  # 3表示计划ID，5为单元id，7为关键词id
    )
    res_by_account = getKeyword10Quality(
        header=user, server=server, body=accountId)
    assert_header(res_by_account.header, STATUS.SUCCESS)
    res_by_account.body.keyword10Quality.sort(key=lambda x: x.id)

    campaignId = GroupId(
        ids=user.get_campaignIds(server),
        type=IDTYPE.CAMPAIGN
    )
    res_by_campaign = getKeyword10Quality(
        header=user, server=server, body=campaignId)
    assert_header(res_by_campaign.header, STATUS.SUCCESS)
    res_by_campaign.body.keyword10Quality.sort(key=lambda x: x.id)

    def assert_func(x, y, key):
        assert x.body == y.body, 'Keyword10Quality by %s differ!\n%s\n%s\n' % (
            key, x.body, y.body)

    assert_func(res_by_account, res_by_campaign, 'campaignIds')

    adgroupId = GroupId(
        ids=user.get_adgroupIds(server),
        type=IDTYPE.ADGROUP
    )
    res_by_adgroup = getKeyword10Quality(
        header=user, server=server, body=adgroupId)
    assert_header(res_by_adgroup.header, STATUS.SUCCESS)
    res_by_adgroup.body.keyword10Quality.sort(key=lambda x: x.id)
    assert_func(res_by_account, res_by_adgroup, 'adgroupIds')

    keywordId = GroupId(
        ids=user.get_keywordIds(server),
        type=IDTYPE.KEYWORD
    )
    res_by_keyword = getKeyword10Quality(
        header=user, server=server, body=keywordId)
    assert_header(res_by_keyword.header, STATUS.SUCCESS)
    res_by_keyword.body.keyword10Quality.sort(key=lambda x: x.id)
    assert_func(res_by_account, res_by_keyword, 'keywordIds')


@mount(api.keyword)
def test_getKeyword(server, user):
    test_getKeywordId(server, user)
    test_getKeywordByAdgroupId(server, user)
    test_getKeywordByKeywordId(server, user)

    test_getKeywordStatus(server, user)
    test_getKeyword10Quality(server, user)

# --------------------------------------------------------------
#  测试更新操作 updateKeyword
# --------------------------------------------------------------


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
    return res


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
def test_updateKeyword_pause(server, user):
    '''
    关键词：更新为暂停状态，不做任何更新
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
def test_updateKeyword_title(server, user):
    '''
    关键词：更新标题为40个字节，返回成功(实际不做修改修改)
    '''
    keyword = GLOBAL[TAG_TYPE]['output']
    change = dict(keyword=gen_chinese_unicode(40))
    _updateKeyword_by_dict(
        server, user, keyword.keywordId, change, {})
    # recovery
    updateKeyword(server=server, header=user, body=keyword)


@formatter
def test_updateKeyword_price_2place(server, user):
    '''
    关键词：更新关键词出价修改为2位小数999.59，测试精度
    '''
    keyword = GLOBAL[TAG_TYPE]['output']
    change = dict(price=999.59)
    _updateKeyword_by_dict(
        server, user, keyword.keywordId, change, change)
    # recovery
    updateKeyword(server=server, header=user, body=keyword)


@formatter
def test_updateKeyword_clear_price(server, user):
    '''
    关键词：更新操作，取消关键词出价，自动更新为单元出价
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
    assert res.body.keywordTypes[0].pause == False, \
        'Activate keyword failed at `%d`!' % keywordId
    # recovery
    updateKeyword(server=server, header=user, body=keyword)


@mount(api.keyword)
def test_updateKeyword(server, user):
    GLOBAL[TAG_TYPE]['output'] = getKeywordByKeywordId(
        header=user, server=server,
        body={'keywordIds': [GLOBAL[TAG_TYPE]['keywordId']]}
    ).body.keywordTypes[0]

    test_updateKeyword_unchange(server, user)
    test_updateKeyword_title(server, user)
    test_updateKeyword_price_2place(server, user)
    test_updateKeyword_clear_price(server, user)
    test_updateKeyword_clear_destinationUrl(server, user)
    test_activeKeyword(server, user)


# ------------------------------------------------------------------------
#  测试删除操作 deleteKeyword
# ------------------------------------------------------------------------


@formatter
def test_deleteKeyword(server, user):
    '''
    TODO: 删除关键词 deleteKeyword
    '''
    res = deleteSublink(
        header=user, server=server,
        body={
            'sublinkIds': [GLOBAL['sublink']['sublinkId']],
            "newCreativeType": TYPE.SUBLINK})
    assert_header(res.header, STATUS.SUCCESS)
    res = getSublinkIdByAdgroupId(
        header=user, server=server,
        body={"adgroupIds": [_get_adgroupId(server, user)]})
    ids = res.body.groupSublinkIds[0].sublinkIds
    assert [] == ids, 'Delete sublinkId failed!\n%s remain existing.\n' % (ids)

# ------------------------------------------------------------------------
#  测试入口
# ------------------------------------------------------------------------


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

log.removeHandler(output_file)
