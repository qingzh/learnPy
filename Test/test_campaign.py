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

import logging
from APITest.models.campaign import *
from APITest import (
    ThreadLocal, log_dec, formatter,
    gen_chinese_unicode, UndefinedException)
from APITest import API_STATUS as STATUS
from APITest.settings import api
from APITest.utils import assert_header, get_log_filename
from functools import update_wrapper
##########################################################################
#    log settings

TAG_TYPE = u'CAMPAIGN'
LOG_FILENAME = get_log_filename(TAG_TYPE)

__loglevel__ = logging.DEBUG
log = logging.getLogger(__name__)
log.setLevel(__loglevel__)

##########################################################################

MAX_CAMPIGN_AMOUNT = 500
SERVER = ThreadLocal.SERVER
USER = ThreadLocal.USER

'''
"campaign": {
    "getAllCampaignId": APIRequest(
        method=post, uri='/api/campaign/getAllCampaignID'),
    "getAllCampaign": APIRequest(
        method=post, uri='/api/campaign/getAllCampaign'),
    "getCampaignByCampaignId": APIRequest(
        method=post, uri='/api/campaign/getCampaignByCampaignId'),
    "updateCampaign": APIRequest(
        method=post, uri='/api/campaign/updateCampaign'),
    "deleteCampaign": APIRequest(
        method=delete, uri='/api/campaign/deleteCampaign'),
    "addCampaign": APIRequest(
        method=post, uri='/api/campaign/addCampaign')
}
'''
locals().update(api.campaign)

# ------------------------------------------------------------------------
# @suite(SUITE.API)  # 动态分配测试集合


class TestCase(object):

    @classmethod
    def decorator(cls, func):
        obj = func.im_self

        def wrapper(*args, **kwargs):
            obj.setUp()
            func(*args, **kwargs)
            obj.tearDown()
        return formatter(update_wrapper(wrapper, func))

    def __init__(self):
        self._testcases = []
        for name in dir(self):
            if name.startswith('test_') is False:
                continue
            method = getattr(self, name, None)
            if method is None:
                continue
            setattr(self, name, TestCase.decorator(method))
            self._testcases.append(name)

    def run(self):
        for name in self._testcases:
            method = getattr(self, name, None)
            if method is None:
                continue
            method()


class CampaignMixin(TestCase):

    def __init__(self, server=None, user=None, uid=None):
        super(CampaignMixin, self).__init__()
        self.server = server or ThreadLocal.SERVER
        self.user = user or ThreadLocal.user
        if uid:
            self.uid = uid
        else:
            pass
            # self.uid = get_uid(user['username'])

    def setUp(self):
        server, user = self.server, self.user
        # response.body: {'campaignIds':[...]}
        ids = user.getAllCampaignId(server=server).body
        if not ids['campaignIds']:
            return
        res = user.deleteCampaign(server=server, body=ids)
        assert_header(res.header)

    tearDown = setUp

    def run(self):
        CampaignMixin.tearDown = lambda x: None
        super(CampaignMixin, self).run()
        CampaignMixin.tearDown = CampaignMixin.setUp
        CampaignMixin.tearDown(self)


class AddCampaignTest(CampaignMixin):

    def _add(self, campaigns):
        ''' 计划：添加，并检查 '''
        server, user = self.server, self.user
        if is_sequence(campaigns) is False:
            campaigns = [campaigns]
        res = user.addCampaign(server=server, body=campaigns)
        ids = list(x.campaignId for x in res.body.campaignTypes)
        # 查询数据库
        res = user.getCampaignByCampaignId(
            server=server, body={'campaignIds': ids})
        for idx, base in enumerate(res.body.campaignTypes):
            expect = campaigns[idx].normalize(campaignId=base.campaignId)
            assert expect == base

    def test_add_default(self):
        ''' 计划：添加计划，使用默认值 '''
        self._add(CampaignType.random())

    def test_add_null(self):
        ''' 计划：添加计划，使用null值 '''
        raise UndefinedException

    def test_add_title01(self):
        ''' 计划：添加计划，名称长度为1 '''
        self._add(CampaignType.random(campaignName='1'))

    def test_add_title02(self):
        ''' 计划：添加计划，名称长度超过30，错误码901202 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(campaignName=gen_chinese_unicode(31))
        res = user.addCampaign(server=server, body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901202)

    def test_add_budget01(self):
        ''' 计划：添加计划，预算为9.99, 错误码901232 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(budget=9.99)
        res = user.addCampaign(server=server, body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901232)

    def test_add_budget02(self):
        ''' 计划：添加计划，预算为500000.01, 错误码901233 '''
        # 计划日预算不能高于500000.0元
        server, user = self.server, self.user
        campaign = CampaignType.random(budget=500000.01)
        res = user.addCampaign(server=server, body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901233)

    def test_add_budget03(self):
        ''' 计划：添加计划，预算为10.49, 测试两位小数 '''
        self._add(CampaignType.random(budget=10.49))

    def test_add_duplicate_name(self):
        ''' 计划：添加计划，名称重复，错误码901203 '''
        # 计划名称已存在
        server, user = self.server, self.user
        campaign = CampaignType.random()
        self._add(campaign)
        res = user.addCampaign(server=server, body=campaign)
        assert_header(res.header, STATUS.FAIL, 901203)

    def test_add_500(self):
        ''' 计划：添加计划500个 '''
        self._add(CampaignType.factory(500))

    def test_add_exceed(self):
        ''' 计划：添加计划，超过500个 '''
        server, user = self.server, self.user
        campaigns = CampaignType.factory(501)
        res = user.addCampaign(server=server, body=campaigns)
        assert_header(res.header, STATUS.FAIL, 901204)


class UpdateCampaignTest(CampaignMixin):

    '''
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

    def setUp(self):
        super(UpdateCampaignTest, self).setUp()
        server, user = self.server, self.user
        res = user.addCampaign(server=server, body=CampaignType.random())
        self.campaignId = res.body.campaignTypes[0].campaignId

    def _update(self, **kwargs):
        ''' 计划：添加，并检查 '''
        server, user = self.server, self.user
        campaignId = kwargs.setdefault('campaignId', self.campaignId)
        # 原计划
        campaign = user.getCampaignByCampaignId(
            server=server, body=CampaignId(self.campaignId)
        ).body.campaignTypes[0]
        campaign = CampaignType(**campaign)
        # 更新计划
        update_campaign = CampaignType(**kwargs)
        res = self.updateCampaign(update_campaign)
        assert_header(res.header)
        # 查询数据库
        res = user.getCampaignByCampaignId(
            server=server, body=CampaignId(campaignId))
        # 对比
        base = res.body.campaignTypes[0]
        expect = campaign.normalize(update_campaign)
        assert expect == base, u'更新后计划和预期不一致\n'\
            u'原来: %s\n更新: %s\n期望: %s\n实际: %s\n' % (
            campaign, kwargs, expect, base)

    def updateCampaign(self, campaign):
        return self.user.updateCampaign(server=self.server, body=campaign)

    def test_update_title01(self):
        """ 计划：更新计划名称为1个字符 """
        self._update(campaignName='1')

    def test_update_title02(self):
        """ 计划：更新计划名称为30个字符 """
        self._update(campaignName=gen_chinese_unicode(30))

    def test_update_title03(self):
        """ 计划：更新计划名称为31个字符，错误码901202 """
        res = self.updateCampaign(CampaignType(
            campaignId=self.campaignId,
            campaignName=gen_chinese_unicode(31)
        ))
        assert_header(res.header, STATUS.FAIL, 901202)

    def test_update_title04(self):
        """ 计划：更新计划名称为相同的用户名，错误码901202 """
        res = self.updateCampaign(CampaignType(
            campaignId=self.campaignId,
            campaignName=gen_chinese_unicode(31)
        ))
        assert_header(res.header, STATUS.FAIL, 901202)

    def test_update_budget01(self):
        ''' 计划：更新计划预算为9.99, 错误码901232 '''
        res = self.updateCampaign(CampaignType(
            campaignId=self.campaignId,
            budget=9.99,
        ))
        assert_header(res.header, STATUS.FAIL, 901232)

    def test_update_budget02(self):
        ''' 计划：更新计划预算为10.49, 正常更新 '''
        self._update(budget=10.49)

    def test_update_budget03(self):
        ''' 计划：更新计划预算为500000.00，正常更新 '''
        self._update(budget=500000.00)

    def test_update_budget04(self):
        ''' 计划：更新计划预算为500000.01, 错误码901233 '''
        res = self.updateCampaign(CampaignType(
            campaignId=self.campaignId,
            budget=500000.01
        ))
        assert_header(res.header, STATUS.FAIL, 901233)

    def test_update_default(self):
        ''' 计划：使用null更新，默认不做任何修改 '''
        self._update(
            campaignName=None,
            budget=None,
            regionTarget=None,
            excludeIp=None,
            negativeWords=None,
            exactNegativeWords=None,
            schedule=None,
            showProb=None,
            pause=None,
        )

    def test_update_pause(self):
        ''' 计划：更新计划状态pause '''
        self._update(pause=True)
        # 默认不修改
        self._update(pause=None)
        self._update(pause=False)
        # 默认不修改
        self._update(pause=None)

    def test_update_regionTarget01(self):
        ''' 计划：更新计划的推广地域 '''
        self._update(regionTarget=[u'北京', u'天津'])
        # 取消限制
        self._update(regionTarget=[u'所有地域'])

    def test_update_excludeIp01(self):
        ''' 计划：更新计划的IP排除 '''
        self._update(excludeIp=['10.9.*.*', '42.120.172.*', '127.0.0.1'])
        # 取消限制
        self._update(excludeIp=['$'])

    def test_update_negativeWords(self):
        """ 计划：更新计划的否定关键词 """
        self._update(negativeWords=[u'否定01', u'否定02'])
        # 取消限制
        self._update(negativeWords=[u'$'])

    def test_update_exactNegativeWords(self):
        """ 计划：更新计划的精确否定关键词 """
        self._update(exactNegativeWords=[u'精确否定', u'否定关键词'])
        # 取消限制
        self._update(exactNegativeWords=['$'])

    def test_upate_schedule01(self):
        """ 计划：更新计划的推广时段 """
        self._update(schedule=[
            Schedule(1, 0, 12),
            Schedule(2, 0, 24),
            Schedule(6, 12, 24),
            Schedule(6, 10, 20)
        ])
        # 取消限制
        self._update(schedule=[
            Schedule(0)
        ])

    def test_update_showProb(self):
        ''' 计划：更新计划的展现方式 '''
        self._update(showProb=1)
        # 默认不修改
        self._update(showProb=None)
        self._update(showProb=0)
        # 默认不修改
        self._update(showProb=None)


@log_dec(log, LOG_FILENAME, __loglevel__)
def test_main(server=None, user=None):
    server = server or ThreadLocal.SERVER
    user = user or ThreadLocal.USER
    AddCampaignTest(server, user).run()
    UpdateCampaignTest(server, user).run()
