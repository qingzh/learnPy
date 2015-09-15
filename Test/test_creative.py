# -*- coding:utf-8 -*-
'''
针对 附加创意 (NewCreative) 接口的回归测试:
'''
from APITest.models.models import (APIData, AttributeDict)
from APITest.models.creative import *
from APITest.settings import SERVER, USERS, api
from APITest.utils import assert_header
import collections
from APITest.models.user import UserObject
from APITest.models.const import STATUS
import threading
import logging
from TestCommon.utils import gen_chinese_unicode
import urlparse
from APITest.compat import (
    formatter, mount, suite, ThreadLocal, BLANK, UndefinedException)
from APITest.utils import get_log_filename
##########################################################################
#    log settings

TAG_TYPE = u'创意'
LOG_FILENAME = get_log_filename(TAG_TYPE)

__loglevel__ = logging.DEBUG
log = logging.getLogger(__name__)
output_file = logging.FileHandler(LOG_FILENAME, 'w')
log.setLevel(__loglevel__)
output_file.setLevel(__loglevel__)
log.addHandler(output_file)

##########################################################################

DEFAULT_USER = UserObject(**USERS.get('wolongtest'))


'''
"creative": {
    "getCreativeIdByAdgroupId": APIRequest(
        method=post, uri='/api/creative/getCreativeIdByAdgroupId'),
    "getCreativeByAdgroupId": APIRequest(
        method=post, uri='/api/creative/getCreativeByAdgroupId'),
    "getCreativeByCreativeId": APIRequest(
        method=post, uri='/api/creative/getCreativeByCreativeId'),
    "getCreativeStatus": APIRequest(
        method=post, uri='/api/creative/getCreativeStatus'),
    "addCreative": APIRequest(
        method=post, uri='/api/creative/addCreative'),
    "updateCreative": APIRequest(
        method=post, uri='/api/creative/updateCreative'),
    "deleteCreative": APIRequest(
        method=delete, uri='/api/creative/deleteCreative'),
    # 区别于activate creatives
    "activateCreative": APIRequest(
        method=post, uri='/api/creative/activeCreative'),
}
'''
locals().update(api.creative)

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
        header=user, body={"adgroupIds": adgroupId}, server=server)
    return res.body


def _compare_dict(a, b):
    for key, value in a.iteritems():
        if value is None:
            continue
        assert value == b[key], 'Content Differ at key `%s`!\n'\
            'Expected: %s\nActually: %s\n' % (key, value, b[key])
    return True

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


def _get_hostname(domain):
    return urlparse.urlparse(domain).hostname


@formatter
def test_addCreative(server, user):
    '''
    创意：添加操作(使用默认值)，预期结果：添加成功
    '''
    # 输入物料
    tag = user.get_tag(TAG_TYPE)
    domain = user.domain(server)
    creative = CreativeType(
        creativeId=None,
        adgroupId=_get_adgroupId(server, user),
        title=gen_chinese_unicode(50),
        description1=gen_chinese_unicode(120),
        destinationUrl=_get_url(domain, tag),
        displayUrl=None,
        pause=None,
        status=None,
    )
    GLOBAL[TAG_TYPE]['input'] = creative
    res = addCreative(
        server=server, header=user, body=creative)
    assert_header(res.header, STATUS.SUCCESS)
    # 这里应该是查询数据库，对比数据

    creative.update(
        creativeId=res.body.creativeTypes[0].creativeId,
        displayUrl=_get_hostname(creative.destinationUrl),
        pause=False,
    )
    GLOBAL[TAG_TYPE]['creativeId'] = creative.creativeId
    res_after = getCreativeByCreativeId(
        server=server, header=user,
        body={"creativeIds": [creative.creativeId]})
    _compare_dict(creative, res_after.body.creativeTypes[0])


# --------------------------------------------------------------
#  测试查询操作 getCreative(.*)
# --------------------------------------------------------------

@formatter
def test_getCreativeId(server, user):
    '''
    创意：获取单元ID下的创意ID getCreativeIdByAdgroupId
    '''
    res = getCreativeIdByAdgroupId(
        server=server, header=user,
        body={'adgroupIds': [GLOBAL[TAG_TYPE]['input']['adgroupId']]})
    assert_header(res.header, STATUS.SUCCESS)
    assert set(res.body.groupCreativeIds[0].creativeIds) == set(
        [GLOBAL[TAG_TYPE]['creativeId']])


@formatter
def test_getCreativeByAdgroupId(server, user):
    '''
    创意：获取单元ID下的所有创意对象 getCreativeByAdgroupId
    '''
    res = getCreativeByAdgroupId(
        header=user, server=server,
        body={'adgroupIds': [GLOBAL[TAG_TYPE]['input']['adgroupId']]})
    assert_header(res.header, STATUS.SUCCESS)
    creative = res.body.groupCreatives[0].creativeTypes[0]
    _compare_dict(GLOBAL[TAG_TYPE]['input'], creative)


@formatter
def test_getCreativeByCreativeId(server, user):
    '''
    创意：通过创意ID获取创意对象 getCreativeByCreativeId
    '''
    res = getCreativeByCreativeId(
        header=user, server=server,
        body={'creativeIds': [GLOBAL[TAG_TYPE]['creativeId']]})
    assert_header(res.header, STATUS.SUCCESS)
    _compare_dict(GLOBAL[TAG_TYPE]['input'], res.body.creativeTypes[0])


# --------------------------------------------------------------
#  测试 getCreativeStatus
# --------------------------------------------------------------


@formatter
def test_getCreativeStatus(server, user):
    '''
    测试了 4 种获取创意状态方法
    按全账户获取，按计划获取，按单元获取，按创意ID获取
    '''
    accountId = GroupId(
        ids=None,
        type=None,  # 3表示计划ID，5为单元id，7为创意id
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

# --------------------------------------------------------------
#  测试更新操作 updateCreative
#  和 创意更新很不一样！
# --------------------------------------------------------------


def _update_by_dict(server, user, creativeId, change, expected):
    # 获取修改后的创意的期望结果
    res = getCreativeByCreativeId(
        header=user, server=server, body={'creativeIds': [creativeId]})
    creative = CreativeType(**res.body.creativeTypes[0])
    creative.update(expected)
    # 修改创意
    change = CreativeType(**change)
    change.update(creativeId=creativeId)
    res = updateCreative(server=server, header=user, body=change)
    assert_header(res.header, STATUS.SUCCESS)
    res_after = getCreativeByCreativeId(
        header=user, server=server, body={'creativeIds': [creativeId]})
    # 对比
    _compare_dict(creative, res_after.body.creativeTypes[0])


@formatter
def test_updateCreative_unchange(server, user):
    '''
    创意：更新操作，不做任何更新
    '''
    creative = GLOBAL[TAG_TYPE]['output']
    change = dict(
        adgroupId=123456,
        title=None,
        description1=None,
        destinationUrl=None,
        displayUrl=None,
        pause=None,
        status=None,
    )
    _update_by_dict(
        server, user, creative.creativeId, change, {})
    # recovery
    updateCreative(server=server, header=user, body=creative)


@formatter
def test_updateCreative_set_title_max_length(server, user):
    '''
    创意：更新描述，测试通配符和换行符
    '''
    creative = GLOBAL[TAG_TYPE]['output']
    change = dict(description1='{%s}\n{%s}\n{%s}' % (
        gen_chinese_unicode(40),
        gen_chinese_unicode(40),
        gen_chinese_unicode(40)
    ))
    expected = dict(description1=change['description1'].replace('\n', ''))
    _update_by_dict(
        server, user, creative.creativeId, change, expected)
    # recovery
    updateCreative(server=server, header=user, body=creative)


@formatter
def test_updateCreative_set_title_min_length(server, user):
    '''
    创意：更新描述，测试包含通配符总长度为8，期望结果：错误提示
    '''
    creative = GLOBAL[TAG_TYPE]['output']
    change = dict(
        description1='{%s}\n{%s}\n{%s}' % (
            gen_chinese_unicode(2),
            gen_chinese_unicode(2),
            gen_chinese_unicode(2)
        ),
        creativeId=creative.creativeId
    )
    res = updateCreative(
        server=server, header=user, body=CreativeType(**change))
    assert_header(res.header, STATUS.FAIL)
    assert 901843 in res.codes


@formatter
def test_activeCreative(server, user):
    '''
    激活创意 activateCreative
    '''
    creative = GLOBAL[TAG_TYPE]['output']
    change = {'pause': True}
    _update_by_dict(server, user, creative.creativeId, change, change)
    res = activateCreative(
        header=user, server=server,
        body={"creativeIds": [creative.creativeId]})
    assert res.body.creativeTypes[0].pause == False, \
        'Activate creative failed at `%d`!' % creativeId
    # recovery
    updateCreative(server=server, header=user, body=creative)


@mount(api.creative)
def test_updateCreative(server, user):
    GLOBAL[TAG_TYPE]['output'] = getCreativeByCreativeId(
        header=user, server=server,
        body={'creativeIds':
              [GLOBAL[TAG_TYPE]['creativeId']]}).body.creativeTypes[0]

    test_updateCreative_unchange(server, user)
    test_updateCreative_set_title_max_length(server, user)
    test_updateCreative_set_title_min_length(server, user)
    test_activeCreative(server, user)


# ------------------------------------------------------------------------
#  测试删除操作 deleteCreative
# ------------------------------------------------------------------------


@formatter
def test_deleteSublink(server, user):
    '''
    推广电话：删除操作 deleteSublink
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
    '''
    主测试入口
    '''
    user.get_tag(TAG_TYPE, refresh=True)
    results = ThreadLocal.get_results()
    len_before = len(results)

    test_addCreative(server, user)
    test_getCreative(server, user)
    test_updateCreative(server, user)
    # test_deleteCreative(server, user)

    flag = all(
        (results[i].status == 'PASS' for i in range(len_before, len(results))))
    flag and recover and _delete_adgroupId(server, user)

log.removeHandler(output_file)
