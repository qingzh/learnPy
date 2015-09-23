#! -*- coding:utf8 -*-
''' TODO
设计一个TextFixure
绑定 服务器，用户名 <不可变>
动态返回 campaignId, adgroupId, sublink等等（动态调用接口获取参数...)
去查数据库！！

'''
from ..settings import api, SERVERS
from .models import AttributeDict, APIData
from ..compat import AttributeDictWithProperty
import uuid
from ..utils import assert_header
from const import STATUS
from functools import partial

__all__ = ["UserObject"]

MAX_BUDGET = 500000 - 10


class UserObject(AttributeDictWithProperty):

    '''
    需要记录为这次测试建立的计划ID，单元ID
    名称为："附加创意"+tag, "附加创意"+tag

    '''

    def __init__(self, username, password, token, target=None, source=None):
        self.username = username
        self.password = password
        self.token = token
        self.target = target
        if source:
            self.source = source
        # tag: 32 bit
        self.__dict__['tag'] = {}
        '''
        # 这里可以修改成动态的，修改参见 __getattr__
        for key, val in api.nodes.iteritems():
            self.__dict__[key] = partial(val.__call__, header=self)
        '''

    def __getattr__(self, key):
        # api 如果改变了也能同步改变
        if key in self.__dict__:
            return self.__dict__[key]
        try:
            return super(UserObject, self).__getattr__(key)
        except Exception as e:
            nodes = api.nodes
            if key in nodes:
                return partial(nodes[key].__call__, header=self)
            raise e

    def get_tag(self, tagType, refresh=False):
        # MAX length = 32
        if refresh or tagType not in self.__dict__['tag']:
            self.__dict__['tag'][tagType] = uuid.uuid4().hex[:16]
        return self.__dict__['tag'][tagType]

    def add_campaign(self, server, prefix=u'匿名'):
        data = APIData(header=self)
        tag = self.get_tag(prefix)
        data.body = {"campaignTypes": [dict(
            # campaignId=num,
            campaignName='%s%s' % (prefix, tag),
            # status=num
        )]}
        res = api.campaign.addCampaign.response(server, json=data)
        try:
            assert_header(res.header, STATUS.SUCCESS)
            return res.body.campaignTypes[0]
        except AssertionError as e:
            if res.header.get('failures', [{}])[0].get('code', 0) != 901203:
                raise e
            self.get_tag(prefix, refresh=True)
            return self.add_campaign(server, prefix)
        except KeyError:
            return res

    def delete_campaign(self, server, campaignId):
        data = APIData(header=self, body={"campaignIds": [campaignId]})
        res = api.campaign.deleteCampaign.response(server, json=data)
        assert_header(res.header, STATUS.SUCCESS)

    def add_adgroup(self, server, prefix=u'匿名'):
        '''
        campaignName: prefix+tag
        adgroupName: prefix+tag

        assert len_unicode(prefix) <= 14

        @return adgroupId
        '''
        campaignType = self.add_campaign(server, prefix)
        data = APIData(header=self)
        tag = self.get_tag(prefix)
        data.body = {"adgroupTypes": [dict(
            campaignId=campaignType.campaignId,
            adgroupName='%s%s' % (prefix, tag),
            maxPrice=int(tag, 16) % 100000 * 0.01 + 0.3,  # [0.3, 999.99]
            adPlatformOS=int(tag, 16) % 7 + 1,
        )]}
        res = api.adgroup.addAdgroup.response(server, json=data)
        return res.body.adgroupTypes[0]

    @property
    def uid(self):
        if '_uid' not in self.__dict__:
            self.__dict__['_uid'] = self.get_account(
                SERVERS.PRODUCTION).accountInfoType.userId
        return self.__dict__['_uid']

    def domain(self, server):
        # 可能是变化的，因为这个domain是可以修改的
        # 调用 /api/account/updateAccount即可以修改
        self.__dict__['_domain'] = domain = self.get_account(
                server).accountInfoType.regDomain
        return domain.split(',')[0]

    def get_account(self, server):
        data = APIData(header=self, body={"requestData": ["account_all"]})
        res = api.account.getAccount.response(server, json=data)
        return res.body

    def get_campaignIds(self, server):
        # body is ignore
        data = APIData(header=self)
        res = api.campaign.getAllCampaignId.response(server, json=data)
        return res.body.campaignIds

    def get_campaignAdgroupIds(self, server):
        # body is ignore
        data = APIData(header=self)
        res = api.adgroup.getAllAdgroupId.response(server, json=data)
        return res.body

    def get_adgroupIds(self, server):
        campaign_adgroups = self.get_campaignAdgroupIds(server)
        if not campaign_adgroups['campaignAdgroupIds']:
            return []
        return reduce(lambda x, y: x + y, (x['adgroupIds']for x in campaign_adgroups['campaignAdgroupIds']))

    def get_keywordIds(self, server):
        data = self._gen_adgroupIds(server)
        if data is None:
            return []
        res = api.keyword.getKeywordIdByAdgroupId(server=server, json=data)
        if not res.body['groupKeywordIds']:
            return []
        return reduce(lambda x, y: x + y, (x['keywordIds']for x in res.body['groupKeywordIds']))

    def get_creativeIds(self, server):
        data = self._gen_adgroupIds(server)
        if data is None:
            return []
        res = api.creative.getCreativeIdByAdgroupId(server=server, json=data)
        if not res.body['groupCreativeIds']:
            return []
        return reduce(lambda x, y: x + y, (x['creativeIds']for x in res.body['groupCreativeIds']))

    def _gen_adgroupIds(self, server):
        ids = self.get_adgroupIds(server)
        if not ids:
            return None
        return APIData(header=self, body={'adgroupIds': ids})

    def get_sublinkIds(self, server):
        data = self._gen_adgroupIds(server)
        if data is None:
            return []
        res = api.newCreative.getSublinkIdByAdgroupId.response(
            server, json=data)
        if not res.body['groupSublinkIds']:
            return []
        return reduce(lambda x, y: x + y, (x['sublinkIds']for x in res.body['groupSublinkIds']))

    def get_appIds(self, server):
        data = self._gen_adgroupIds(server)
        if data is None:
            return []
        res = api.newCreative.getAppIdByAdgroupId.response(
            server, json=data)
        if not res.body['groupAppIds']:
            return []
        return reduce(lambda x, y: x + y, (x['appIds']for x in res.body['groupAppIds']))

    def get_phoneIds(self, server):
        data = self._gen_adgroupIds(server)
        if data is None:
            return []
        res = api.newCreative.getPhoneIdByAdgroupId.response(
            server, json=data)
        if not res.body['groupPhoneIds']:
            return []
        return reduce(lambda x, y: x + y, (x['phoneIds']for x in res.body['groupPhoneIds']))
