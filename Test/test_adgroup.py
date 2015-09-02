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
import json
import logging
import time
from APITest.models.models import AttributeDict, APIData
from APITest.utils import (
    SafeConfigParser, sub_commas, md5_of_file, assert_object)
from TestCommon.models.const import STDOUT, BLANK
from APITest.models.campaign import yield_campaignType
import random
from APITest.settings import SERVER, USERS, api
from APITest.models.adgroup import *
from APITest.utils import assert_header
from APITest.models.user import UserObject
from APITest.models.const import STATUS
from TestCommon import ThreadLocal
from APITest import settings


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
STDOUT.setLevel(logging.INFO)
log.addHandler(STDOUT)

MAX_CAMPIGN_AMOUNT = 500
MAX_ADGROUP_PER_CAMPAIGN = 2000


'''
    "adgroup": {
        "getAllAdgroupId": APIRequest(method=post, uri='/api/adgroup/getAllAdgroupId'),
        "getAdgroupIdByCampaignId": APIRequest(method=post, uri='/api/adgroup/getAdgroupIdByCampaignId'),
        "getAdgroupByCampaignId": APIRequest(method=post, uri='/api/adgroup/getAdgroupByCampaignId'),
        "getAdgroupByAdgroupId": APIRequest(method=post, uri='/api/adgroup/getAdgroupByAdgroupId'),
        "addAdgroup": APIRequest(method=post, uri='/api/adgroup/addAdgroup'),
        "updateAdgroup": APIRequest(method=post, uri='/api/adgroup/updateAdgroup'),
        "deleteAdgroup": APIRequest(method=delete, uri='/api/adgroup/deleteAdgroup'),
    }
'''
locals().update(api.campaign)
locals().update(api.adgroup)

TAG_TYPE = u'单元'
SERVER = settings.SERVER.PRODUCTION
DEFAULT_USER = UserObject(**USERS.get('wolongtest'))

#-------------------------------------------------------------------------
#
#-------------------------------------------------------------------------


def parse_update_map(update_map):
    '''
    @param update_map: dict{
        key:{
            old_value: new_value
        }
    }
    @return set_list, new_list

    TODO: deal with nested dict value
    '''
    set_list, new_list = [], []
    for key, value_map in update_map.iteritems():
        for set_value, new_value in value_map.iteritems():
            set_list.append({key: json.loads(set_value)})
            new_list.append({key: json.loads(new_value)})
    return set_list, new_list


def test_delete_all(params={}, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    删除所有计划
    '''
    get_bd = getAllCampaignID(server=server, header=user)
    del_bd = deleteCampaign(server=server, header=user, body=get_bd.body)
    all_bd = getAllCampaignID(server=server, header=user)
    assert 0 == del_bd.body.result
    assert [] == all_bd.body.campaignIds


def test_delete_subset(server=SERVER, user=DEFAULT_USER, recover=False):
    get_bd = getAllCampaignID(server=server, header=user)
    n = len(get_bd.body.campaignIds)
    if n == 0:
        n = random.randint(1, MAX_CAMPIGN_AMOUNT)
        add_bd = _add_ncampaign(n)
        campaignIds = map(lambda x: x.get('campaignId'),
                          add_bd.body.campaignTypes)
    else:
        campaignIds = get_bd.body.campaignIds
    del_ids = random.sample(campaignIds, random.randint(1, n))
    del_bd = doRequest(deleteCampaign, body={'campaignIds': del_ids})
    assert_success(del_bd)
    all_ids = getAllCampaignID(server=server, header=user).body.campaignIds
    assert [] == filter(lambda x: x in all_ids, del_ids)


def test_delete_mixed(server=SERVER, user=DEFAULT_USER, recover=False):
    get_bd = getAllCampaignID(server=server, header=user)
    n = len(get_bd.body.campaignIds)
    if n == 0:
        n = random.randint(1, MAX_CAMPIGN_AMOUNT)
        add_bd = _add_ncampaign(n)
        campaignIds = map(lambda x: x.get('campaignId'),
                          add_bd.body.campaignTypes)
    else:
        campaignIds = get_bd.body.campaignIds
    del_ids = sorted(random.sample(campaignIds, random.randint(1, n)))
    invalid_ids = [del_ids[0] - i for i in xrange(random.randint(1, n))]
    del_bd = doRequest(
        deleteCampaign, body={'campaignIds': del_ids + invalid_ids})
    assert_partial(del_bd)
    all_ids = getAllCampaignID(server=server, header=user).body.campaignIds
    print del_ids, all_ids
    assert [] == filter(lambda x: x in all_ids, del_ids)
    print del_bd.body.campaignIds, invalid_ids
    assert sorted(del_bd.body.campaignIds) == sorted(invalid_ids)


def test_add_ncampaign(n, server=SERVER, user=DEFAULT_USER, recover=False):
    _delete_all()
    add_bd = _add_ncampaign(n)
    campaignIds = map(lambda x: x.get('campaignId'),
                      add_bd.body.campaignTypes)
    get_bd = doRequest(
        getCampaignByCampaignId, body=dict(campaignIds=campaignIds))
    all_bd = doRequest(getAllCampaign)
    assert_object(add_bd.body, get_bd.body)
    assert_object(add_bd.body, all_bd)


def test_add_exceed(server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    插入计划数超过500, status_code=404
    '''
    all_before = getAllCampaignID(server=server, header=user)
    n = random.randint(MAX_CAMPIGN_AMOUNT, MAX_CAMPIGN_AMOUNT << 1)
    add_bd = _add_ncampaign(n)
    assert_failure(add_bd)
    all_after = getAllCampaignID(server=server, header=user)
    assert all_before.body == all_after.body, '[BEFORE]: %s\n[AFTER]: %s\n' % (
        all_before.body.json(), all_after.body.json())


def _get_campaignId(server, user, refresh=False):
    tag = user.get_tag(TAG_TYPE, refresh)
    tag_dict = ThreadLocal.get_tag_dict((server, user.username), tag)
    if 'campaignId' not in tag_dict:
        tag_dict.update(user.add_campaign(server, TAG_TYPE))
    return tag_dict['campaignId']


def test_getAllAdgroupId(server, user):
    " 获取账户下所有单元ID "
    # return campaignAdgroupIds:[]
    res = getAllAdgroupId(server=server, header=user)
    assert_header(res.header, STATUS.SUCCESS)


def test_getAdgroupIdByCampaignId(server=SERVER, user=DEFAULT_USER, recover=False):
    " 获取计划ID下所有单元ID "
    # return campaignAdgroupIds:[int,]
    res = getAdgroupIdByCampaignId(
        server=server, header=user, body={'campaignIds': user.get_campaignIds(server)})
    assert_header(res.header, STATUS.SUCCESS)


def test_getAdgroupByCampaignId(server=SERVER, user=DEFAULT_USER, recover=False):
    " 获取计划ID下所有单元ID "
    # return campaignAdgroups:[dict,]
    res = getAdgroupByCampaignId(
        server=server, header=user, body={'campaignIds': user.get_campaignIds(server)})
    assert_header(res.header, STATUS.SUCCESS)


def _add_ncampaign(n, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    添加1个合法计划
    '''
    campaigns = list(yield_campaignType(n))
    add_bd = doRequest(addCampaign, body={'campaignTypes': campaigns})
    # all campaigns would be return both failed or successed
    # except len(campaigns) > 500
    if n <= MAX_CAMPIGN_AMOUNT:
        # campaigns should be subset of `ccampaignTypes`
        assert campaigns <= add_bd.body.campaignTypes
    else:
        assert add_bd.header.status == 2
        assert 901204 in add_bd.codes
    return add_bd


def _get_campaign_ids(n, server=SERVER, user=DEFAULT_USER, recover=False):
    campaign_ids = getAllCampaignID(
        server=server, header=user).body.campaignIds
    fixed = n - len(campaign_ids)
    if fixed > 0:
        campaign_ids.extend(_add_ncampaign(fixed).body.campaignIds)
    return random.sample(campaign_ids, n)


def _del_adgroups_by_campaignId(ids):
    adgroup_ids = list(_get_all_adgroup_ids(ids))
    del_bd = _del_adgroup_ids(adgroup_ids, ids)


def _add_adgroup(campaignId, n):
    adgroups = list(yield_adgroupTypes(n))
    map(lambda x: x.update(campaignId=campaignId), adgroups)
    add_bd = doRequest(addAdgroup, body={'adgroupTypes': adgroups})
    return add_bd
    if n < MAX_ADGROUP_PER_CAMPAIGN:
        assert add_bd.body == addAdgroup.body
    else:
        assert add_bd.header.status == 2
        assert 901204 in add_bd.codes


def _get_all_adgroup_ids(ids=None):
    if ids is None:
        get_bd = doRequest(getAllAdgroupId)
    else:
        id_list = list(ids) if isinstance(ids, (list, tuple, set)) else [ids]
        get_bd = doRequest(
            getAdgroupIdByCampaignId, dict(campaignIds=id_list))
    all_ids = set()
    for d in get_bd.body.campaignAdgroupIds:
        all_ids.update(d.get('adgroupIds'))
    return all_ids


def _del_adgroup_ids(id_list, campaignId=None):
    ids_before = _get_all_adgroup_ids(campaignId)
    del_bd = doRequest(deleteAdgroup, dict(adgroupIds=id_list))
    id_deleted = ids_before.intersection(id_list)
    # assert delete failed
    id_failed = set(id_list).difference(id_deleted)
    if id_failed:
        assert set(del_bd.body.adgroupIds) == id_failed
    # assert delete success
    ids_after = _get_all_adgroup_ids(campaignId)
    assert ids_after.isdisjoint(id_deleted)
    return del_bd


def _delete_all(params={}, server=SERVER, user=DEFAULT_USER, recover=False):
    '''
    清空账户计划
    '''
    get_bd = doRequest(getAllCampaignID, params)
    if get_bd.body.campaignIds:
        del_bd = doRequest(deleteCampaign, get_bd.body)
    else:
        return get_bd
    return get_bd, del_bd


def test_main():
    test_add_ncampaign(1)
    test_delete_subset()
    test_add_ncampaign(random.randint(1, MAX_CAMPIGN_AMOUNT))
    test_delete_all()
    test_add_ncampaign(MAX_CAMPIGN_AMOUNT)
    test_delete_subset()
    test_delete_mixed()
    test_add_exceed()
    test_delete_all()
