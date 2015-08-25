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

TAG_TYPE = u'关键词'
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
"keyword": {
    "getKeywordIdByAdgroupId": APIRequest(method=post, uri='/api/keyword/getKeywordIdByAdgroupId'),
    "getKeywordByAdgroupId": APIRequest(method=post, uri='/api/keyword/getKeywordByAdgroupId'),
    "getKeywordByKeywordId": APIRequest(method=post, uri='/api/keyword/getKeywordByKeywordId'),
    "getKeywordStatus": APIRequest(method=post, uri='/api/keyword/getKeywordStatus'),
    "getKeyword10Quality": APIRequest(method=post, uri='/api/keyword/getKeyword10Quality'),
    "addKeyword": APIRequest(method=post, uri='/api/keyword/addKeyword'),
    "updateKeyword": APIRequest(method=post, uri='/api/keyword/updateKeyword'),
    "deleteKeyword": APIRequest(method=delete, uri='/api/keyword/deleteKeyword'),
    "activateKeyword": APIRequest(method=post, uri='/api/keyword/activateKeyword'),
}
'''
locals().update(api.keyword)

#-------------------------------------------------------------------------
# 准备测试数据
# description 总长
# 字典里存的是json形式，因为list不能hash
#-------------------------------------------------------------------------

_local_ = threading.local()
GLOBAL = _local_.__dict__.setdefault('global', {})

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


@formatter
def test_addKeyword(server, user):
    '''
    关键词：添加操作(2条子链)，预期结果：添加成功
    '''
    # 输入物料
    tag = user.get_tag(TAG_TYPE)
    keyword = KeywordType(
        keywordId=None,
        adgroupId=_get_adgroupId(server, user),
        keyword=gen_chinese_unicode(40),
        price=0.3,
        destinationUrl=_get_url(user.domain(server), tag),
        matchType=0,
        pause=True,
        status=None,
    )
    res = addKeyword(
        server=server, header=user, body=keyword)
    assert_header(res.header, STATUS.SUCCESS)
    # 这里应该是查询数据库，对比数据
    GLOBAL['keyword'] = {
        'input': keyword, 'keywordId': res.body.keywordTypes[0].keywordId}


@formatter
def test_getKeywordId(server, user):
    '''
    关键词：获取单元ID下的关键词ID getKeywordIdByAdgroupId
    '''
    res = getKeywordIdByAdgroupId(
        header=user, body={'adgroupIds': [_get_adgroupId(server, user)]}, server=server)
    assert_header(res.header, STATUS.SUCCESS)
    assert set(res.body.groupKeywordIds[0].keywordIds) == set(
        [GLOBAL['keyword']['keywordId']])


@formatter
def test_getKeywordByAdgroupId(server, user):
    '''
    关键词：获取单元ID下的所有关键词对象 getKeywordByAdgroupId
    '''
    res = getKeywordByAdgroupId(
        header=user, server=server, body={'adgroupIds': [GLOBAL['keyword']['input']['adgroupId']]})
    assert_header(res.header, STATUS.SUCCESS)
    keyword = res.body.groupKeywords[0]
    # It's IMPORTANT to convert `keyword` to `KeywordType`
    GLOBAL['keyword']['output'] = keyword
    # TODO
    # 后端传回来的price精度有问题
    assert GLOBAL['keyword']['input'] <= keyword, 'Keyword content differ!\nExpected: %s\nActually: %s\n' % (
        GLOBAL['keyword']['input'], keyword)


def _updateSublink_and_assert(server, user, sublink):
    '''
    推广子链：更新操作，检查更新后的内容
    '''
    if not isinstance(sublink, SublinkType):
        sublink = SublinkType(**sublink)
    sublinkId = sublink.sublinkId
    res = updateSublink(header=user, server=server, body=sublink)
    assert_header(res.header, STATUS.SUCCESS)
    res = getSublinkBySublinkId(
        header=user, server=server, body={'sublinkIds': [sublinkId]})
    res_sublink = res.body.sublinkTypes[0]
    assert res_sublink == sublink, 'Sublink content differ!\nExpected: %s\nActually: %s\n' % (
        sublink, res_sublink)
    GLOBAL['sublink']['output'] = sublink


@formatter
def test_updateSublink_2to4(server, user):
    '''
    推广子链：更新操作，2条变4条
    '''
    tag = user.get_tag(TAG_TYPE)
    sublink = GLOBAL['sublink']['output']
    sublink.update(
        sublinkInfos=[
            SublinkInfo(
                gen_chinese_unicode(8), _get_url(user.domain(server), tag + '/2to4')),
            SublinkInfo(
                gen_chinese_unicode(8), _get_url(user.domain(server), tag + '/2to4')),
            SublinkInfo(
                gen_chinese_unicode(8), _get_url(user.domain(server), tag + '/2to4')),
            SublinkInfo(
                gen_chinese_unicode(8), _get_url(user.domain(server), tag + '/2to4')),
        ],
        pause=True,
        status=0,
    )
    _updateSublink_and_assert(server, user, sublink)


@formatter
def test_updateSublink_4to3(server, user):
    '''
    推广子链：更新操作，4条变成3条
    '''
    tag = user.get_tag(TAG_TYPE)
    sublink = GLOBAL['sublink']['output']
    sublink.update(
        sublinkInfos=[
            SublinkInfo(
                gen_chinese_unicode(8), _get_url(user.domain(server), tag + '/4to3')),
            SublinkInfo(
                gen_chinese_unicode(8), _get_url(user.domain(server), tag + '/4to3')),
            SublinkInfo(
                gen_chinese_unicode(8), _get_url(user.domain(server), tag + '/4to3')),
        ],
        pause=True,
        status=0,
    )
    _updateSublink_and_assert(server, user, sublink)


def test_updateSublink(server, user):
    res = getSublinkBySublinkId(
        header=user, server=server, body={'sublinkIds': [GLOBAL['sublink']['sublinkId']]})
    assert_header(res.header, STATUS.SUCCESS)
    GLOBAL['sublink']['output'] = res.body.sublinkTypes[0]
    test_updateSublink_2to4(server, user)
    test_updateSublink_4to3(server, user)


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


@formatter
def test_addSublink_four(server, user):
    ''' 正常添加推广子链(4个子链)，预期结果：添加成功 '''
    # 输入物料
    raise UndefinedException


#-------------------------------------------------------------------------
#  推广APP
#-------------------------------------------------------------------------

@formatter
def test_addApp(server, user):
    '''
    推广APP：添加操作
    '''
    # 输入物料
    app = AppType(
        appId=None,
        adgroupId=_get_adgroupId(server, user),
        appName=gen_chinese_unicode(8),
        appLogo=image.PNG,
        downloadAddrIOS='http://ios.com.cn/test123',
        downloadAddrAndroid='http://android.com.cn/test123',
        detailAddrAndroid='http://detail.android.com.cn/test123',
        pause=True,
        status=None
    )
    res = addApp(server=server, header=user, body=app)
    assert_header(res.header, STATUS.SUCCESS)
    '''
    res = doRequest(getAppByAppId, server=server, user=user, body={
        "appIds": [res.body.appTypes[0].appId]})
    assert res.body.appTypes[
        0] >= app, u'增加内容和传入不一致:\n%s\n%s\n' % (res.body, app)
    '''
    app.pop('imgFormat')
    app.pop('appLogo')
    GLOBAL['app'] = {'input': app, 'appId': res.body.appTypes[0].appId}


@formatter
def test_getAppId(server, user):
    '''
    推广APP：获取1个单元ID下的推广APP getAppIdByAdgroupId
    '''
    res = getAppIdByAdgroupId(
        header=user, body={'adgroupIds': [_get_adgroupId(server, user)]}, server=server)
    assert_header(res.header, STATUS.SUCCESS)
    assert set(res.body.groupAppIds[0].appIds) == set(
        [GLOBAL['app']['appId']]), 'appId differ! Expected %s, got %s.\n' % (GLOBAL['app']['appId'], res.body.groupAppIds[0].appIds)


@formatter
def test_getAppId_(server, user):
    '''
    推广APP：获取多个单元ID下的推广APP getAppIdByAdgroupId
    '''
    raise UndefinedException


@formatter
def test_getApp(server, user):
    '''
    推广APP：根据APP ID查询 getAppByAppId
    '''
    res = getAppByAppId(
        header=user, server=server, body={'appIds': [GLOBAL['app']['appId']]})
    assert_header(res.header, STATUS.SUCCESS)
    assert GLOBAL['app']['input'] <= res.body.appTypes[
        0], 'App content differ!\nExpected: %s\nActually: %s\n' % (GLOBAL['app']['input'], res.body.appTypes[0])


@formatter
def test_deleteApp(server, user):
    '''
    推广APP：删除操作 deleteApp
    '''
    res = deleteSublink(
        header=user, server=server, body={'sublinkIds': [GLOBAL['app']['appId']], "newCreativeType": TYPE.APP})
    assert_header(res.header, STATUS.SUCCESS)
    res = getAppIdByAdgroupId(
        header=user, server=server, body={"adgroupIds": [_get_adgroupId(server, user)]})
    ids = res.body.groupAppIds[0].appIds
    assert [] == ids, 'Delete appId failed!\n%s remain existing.\n' % (ids)


#-------------------------------------------------------------------------
#  推广电话
#-------------------------------------------------------------------------

@formatter
def test_addPhone(server, user):
    '''
    推广电话：添加操作
    '''
    phone = PhoneType(
        phoneId=None,
        phoneNum='010-%s' % (
            10000000 + int(user.get_tag(TAG_TYPE), 16) % 10000007),
        adgroupId=_get_adgroupId(server, user),
        pause=True,
        status=None,
    )
    res = addPhone(server=server, header=user, body=phone)
    assert_header(res.header, STATUS.SUCCESS)
    '''
    res = doRequest(getPhoneByPhoneId, server=server, user=user, body={
        "phoneIds": [res.body.phoneTypes[0].phoneId]})
    assert res.body.phoneTypes[
        0] >= phone, u'增加内容和传入不一致:\n%s\n%s\n' % (res.body, phone)
    '''
    GLOBAL['phone'] = {
        'input': phone, 'phoneId': res.body.phoneTypes[0].phoneId}


@formatter
def test_getPhoneId(server, user):
    '''
    推广电话：获取单元ID下的推广电话 getPhoneIdByAdgroupId
    '''
    res = getPhoneIdByAdgroupId(
        header=user, body={'adgroupIds': [_get_adgroupId(server, user)]}, server=server)
    assert_header(res.header, STATUS.SUCCESS)
    assert set(res.body.groupPhoneIds[0].phoneIds) == set(
        [GLOBAL['phone']['phoneId']])


@formatter
def test_getPhone(server, user):
    '''
    推广电话：根据电话ID查询 getPhoneByPhoneId
    '''
    res = getPhoneByPhoneId(
        header=user, server=server, body={'phoneIds': [GLOBAL['phone']['phoneId']]})
    assert_header(res.header, STATUS.SUCCESS)
    assert GLOBAL['phone']['input'] <= res.body.phoneTypes[
        0], 'Phone content differ!\nExpected: %s\nActually: %s\n' % (GLOBAL['phone']['input'], res.body.phoneTypes[0])


@formatter
def test_deletePhone(server, user):
    '''
    推广电话：删除操作 deletePhone
    '''
    res = deleteSublink(
        header=user, server=server, body={'sublinkIds': [GLOBAL['phone']['phoneId']], "newCreativeType": TYPE.PHONE})
    assert_header(res.header, STATUS.SUCCESS)
    res = getPhoneIdByAdgroupId(
        header=user, server=server, body={"adgroupIds": [_get_adgroupId(server, user)]})
    ids = res.body.groupPhoneIds[0].phoneIds
    assert [] == ids, 'Delete phoneId failed!\n%s remain existing.\n' % (ids)


def mount(obj):
    def decorator(func):
        obj.__dict__[func.__name__] = func

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator

#-------------------------------------------------------------------------
#  测试入口
#-------------------------------------------------------------------------


@mount(api.newCreative)
def test_app(server, user):
    test_addApp(server, user)
    test_getAppId(server, user)
    test_getApp(server, user)
    test_deleteApp(server, user)


@mount(api.newCreative)
def test_phone(server, user):
    test_addPhone(server, user)
    test_getPhoneId(server, user)
    test_getPhone(server, user)
    test_deletePhone(server, user)


@mount(api.newCreative)
def test_sublink(server, user):
    test_addSublink(server, user)
    test_getSublinkId(server, user)
    test_getSublink(server, user)
    test_updateSublink(server, user)
    test_deleteSublink(server, user)


@mount(api.newCreative)
def test_main(server=SERVER, user=DEFAULT_USER, recover=True):
    user.get_tag(TAG_TYPE, refresh=True)
    results = ThreadLocal.get_results()
    len_before = len(results)

    test_app(server, user)
    test_phone(server, user)
    test_sublink(server, user)

    flag = all(
        (results[i].status == 'PASS' for i in range(len_before, len(results))))
    flag and recover and _delete_adgroupId(server, user)
