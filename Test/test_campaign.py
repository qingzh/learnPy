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
    ThreadLocal, log_dec, formatter, TestCase,
    gen_chinese_unicode, UndefinedException, is_sequence)
from APITest import API_STATUS as STATUS
from APITest.settings import api
from APITest.utils import assert_header, get_log_filename
from functools import partial

##########################################################################
#    log settings

TAG_TYPE = u'CAMPAIGN'
LOG_FILENAME = get_log_filename(TAG_TYPE)

__loglevel__ = logging.DEBUG
log = logging.getLogger(__name__)
log.setLevel(__loglevel__)

##########################################################################

SERVER = ThreadLocal.SERVER
USER = ThreadLocal.USER

'''
"campaign": {
    "getAllCampaignId": APIRequest(
        method=post, uri='/api/campaign/getAllCampaignID'),
    "getAllCampaign": APIRequest(
        method=post, uri='/api/campaign/getAllCampaign'),
    "getCampaignByCampaignId": APIRequest(
        method=post, uri='/api/campaign/self.getCampaignByCampaignId'),
    "updateCampaign": APIRequest(
        method=post, uri='/api/campaign/self.updateCampaign'),
    "deleteCampaign": APIRequest(
        method=delete, uri='/api/campaign/self.deleteCampaign'),
    "addCampaign": APIRequest(
        method=post, uri='/api/campaign/self.addCampaign')
}
'''
env = locals()

def setup_env(source, **kwargs):
    for key, value in source.items():
        env[key] = partial(value, **kwargs)

# ------------------------------------------------------------------------
# @suite(SUITE.API)  # 动态分配测试集合


class CampaignMixin(TestCase):

    def setup_env(self, source):
        for key, value in source.items():
            self.__dict__[key] = partial(
                value, server=self.server, header=self.user)

    def __init__(self, server=None, user=None, uid=None):
        super(CampaignMixin, self).__init__()
        self.server = server or ThreadLocal.SERVER
        self.user = user or ThreadLocal.user
        self.setup_env(api.campaign)

        if uid:
            self.uid = uid
        else:
            pass
            # self.uid = get_uid(user['username'])

    def setUp(self):
        '''
        应当转化为数据库操作
        '''
        server, user = self.server, self.user
        # response.body: {'campaignIds':[...]}
        ids =self.getAllCampaignId().body
        if not ids['campaignIds']:
            return
        res = self.deleteCampaign(body=ids)
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
        res = self.addCampaign(body=campaigns)
        assert_header(res.header, STATUS.SUCCESS)
        ids = list(x.campaignId for x in res.body.campaignTypes)
        # 查询数据库
        res = self.getCampaignByCampaignId(body={'campaignIds': ids})
        for idx, base in enumerate(res.body.campaignTypes):
            expect = campaigns[idx].normalize(campaignId=base.campaignId)
            assert expect == base, 'Expected: {}\nActually: {}'.format(
                expect, base)

    def test_default(self):
        ''' 计划：添加计划，使用默认值 '''
        self._add(CampaignType.random())

    def test_null(self):
        ''' 计划：添加计划，使用null值 '''
        raise UndefinedException

    def test_id01(self):
        ''' 计划：添加计划，计划ID乱填，应该正常添加(ID被无视) '''
        self._add(CampaignType.random(campaignId='abc'))

    def test_title01(self):
        ''' 计划：添加计划，名称长度为1 '''
        self._add(CampaignType.random(campaignName='1'))

    def test_title02(self):
        ''' 计划：添加计划，名称长度超过30，错误码901202 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(campaignName=gen_chinese_unicode(31))
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901202)

    def test_title03(self):
        ''' 计划：添加计划，名称为空字符串，错误码901201 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(campaignName='')
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901201)

    def test_budget01(self):
        ''' 计划：添加计划，预算为9.99, 错误码901232 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(budget=9.99)
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901232)

    def test_budget02(self):
        ''' 计划：添加计划，预算为500000.01, 错误码901233 '''
        # 计划日预算不能高于500000.0元
        server, user = self.server, self.user
        campaign = CampaignType.random(budget=500000.01)
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901233)

    def test_budget03(self):
        ''' 计划：添加计划，预算为10.49, 测试两位小数 '''
        self._add(CampaignType.random(budget=10.49))

    def test_budget04(self):
        ''' 计划：添加计划，预算为-1, 错误码901232 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(budget='-1.0')
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901232)

    def test_region01(self):
        ''' 计划：添加计划，地域为'所有地域' '''
        self._add(CampaignType.random(regionTarget=[u'所有地域']))

    def test_region02(self):
        ''' 计划：添加计划，地域为'北京;江苏-南京' '''
        self._add(CampaignType.random(regionTarget=[u'北京',u'江苏-南京']))

    def test_region03(self):
        ''' 计划：添加计划，地域为'你好', 错误码901243 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(regionTarget=[u'你好'])
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901243)

    def test_region04(self):
        ''' 计划：添加计划，地域为'江苏;江苏-南京', 错误码901243 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(regionTarget=[u'江苏', u'江苏-南京'])
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901243)

    def test_region05(self):
        ''' 计划：添加计划，地域为'南京', 错误码901243 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(regionTarget=[u'南京'])
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901243)

    def test_region06(self):
        ''' 计划：添加计划，地域为空集[] '''
        self._add(CampaignType.random(regionTarget=[]))

    def test_region07(self):
        ''' 计划：添加计划，地域为空串'', 错误码901243 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(regionTarget=[''])
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901243)

    def test_negativeWords01(self):
        ''' 计划：添加计划，否定关键词长度为40个字符
        现存BUG：字面里的小写字母有部分会被转化为大写字母 '''
        self._add(CampaignType.random(negativeWords=[gen_chinese_unicode(40)]))

    def test_negativeWords02(self):
        ''' 计划：添加计划，否定关键词超过40个字符, 错误码901253 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(negativeWords=[u'否定01', gen_chinese_unicode(41)])
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901253)

    def test_negativeWords03(self):
        ''' 计划：添加计划，否定关键词正好200个 '''
        self._add(CampaignType.random(
            negativeWords=list(str(x) for x in range(200))))

    def test_negativeWords04(self):
        ''' 计划：添加计划，否定关键词超过200个, 错误码901251 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(
            negativeWords=list(str(x) for x in range(201)))
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901251)

    def test_exactNegativeWords01(self):
        ''' 计划：添加计划，精确否定关键词长度为40个字符 '''
        self._add(CampaignType.random(
            exactNegativeWords=[gen_chinese_unicode(40)]))

    def test_exactNegativeWords02(self):
        ''' 计划：添加计划，精确否定关键词超过40个字符, 错误码901254 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(
            exactNegativeWords=[u'精确否定01', gen_chinese_unicode(41)])
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901254)

    def test_exactNegativeWords03(self):
        ''' 计划：添加计划，精确否定关键词长度为200个 '''
        self._add(CampaignType.random(
            exactNegativeWords=list(str(x) for x in range(200))))

    def test_exactNegativeWords04(self):
        ''' 计划：添加计划，精确否定关键词超过200个, 错误码901252 '''
        server, user = self.server, self.user
        campaign = CampaignType.random(
            exactNegativeWords=list(str(x) for x in range(201)))
        res = self.addCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901252)

    def test_excludeIp01(self):
        ''' 计划：更新排除IP为 '1.1.1.*;1.1.*.*;127.0.0.1;0.0.0.0' '''
        self._add(CampaignType.random(
            excludeIp=['1.1.1.*', '1.1.*.*', '127.0.0.1', '0.0.0.0']))

    def test_excludeIp02(self):
        ''' 计划：更新排除IP为 '1.1.1.*;127.0.0.1;1.1.1.*;127.0.0.1;'
        自动去重 '''
        self._add(CampaignType.random(
            excludeIp=['1.1.1.*', '127.0.0.1', '1.1.1.*', '127.0.0.1']))

    def _expect_fail(self, code, **kwargs):
        server, user = self.server, self.user
        campaign = CampaignType.random(**kwargs)
        res = self.addCampaign(body=campaign)
        assert_header(res.header, STATUS.FAIL, code)

    def test_excludeIp03(self):
        ''' 计划：更新排除IP为 '1.2.3.4.5' '''
        self._expect_fail(901273, excludeIp=['1.2.3.4.5'])
    def test_excludeIp04(self):
        ''' 计划：更新排除IP为 '1.2.3.' '''
        self._expect_fail(901273, excludeIp=['1.2.3.'])
    def test_excludeIp05(self):
        ''' 计划：更新排除IP为 '1.*.*.*' '''
        self._expect_fail(901273, excludeIp=['1.*.*.*'])
    def test_excludeIp06(self):
        ''' 计划：更新排除IP为 '1.1.*.1' '''
        self._expect_fail(901273, excludeIp=['1.1.*.1'])
    def test_excludeIp07(self):
        ''' 计划：更新排除IP为 '1.0.0.256' '''
        self._expect_fail(901273, excludeIp=['1.0.0.256'])
    def test_excludeIp08(self):
        ''' 计划：更新排除IP为 '*' '''
        self._expect_fail(901273, excludeIp=['*'])

    def test_schedule01(self):
        ''' 计划：添加计划，推广时段为空集[]
        结果推广时段是：全部时段，正确否？ '''
        self._add(CampaignType.random(schedule=[]))

    def test_schedule02(self):
        ''' 计划：添加计划，推广时段为空串[''] '''
        self._add(CampaignType.random(schedule=['']))

    def test_schedule03(self):
        ''' 计划：添加计划，推广时段为null '''
        self._add(CampaignType.random(schedule=None))

    def test_schedule04(self):
        ''' 计划：添加计划，推广时段为[110-110] 
        结束时间 = 开始时间 '''
        self._add(CampaignType.random(schedule=['110-110']))
    def test_schedule05(self):
        ''' 计划：添加计划，推广时段为[219-210]
        结束时间 < 开始时间 '''
        self._expect_fail(901295, schedule=['219-210'])

    def test_schedule06(self):
        ''' 计划：添加操作，设置12个推广时间 ''' 
        self._add(CampaignType.random(schedule=[
            '100-109', '110-111', '111-112', '112-113','113-114',
            '114-115', '115-116', '116-117', '117-118', '118-119',
            '119-120', '120-121']))

    def test_schedule07(self):
        ''' 计划：添加计划，推广时间超过12个 ''' 
        self._expect_fail(901234, schedule=[
            '100-109', '110-111', '211-212', '112-113','213-214',
            '114-115', '215-216', '116-117', '217-218', '118-119',
            '219-220', '120-121', '221-222'])

    def test_shcedule08(self):
        ''' 计划：添加计划，推广时段有重叠 '''
        self._add(CampaignType.random(schedule=['710-717', '715-718']))


    def test_duplicate_name(self):
        ''' 计划：添加计划，名称重复，错误码901203 '''
        # 计划名称已存在
        server, user = self.server, self.user
        campaign = CampaignType.random()
        self._add(campaign)
        res = self.addCampaign(body=campaign)
        assert_header(res.header, STATUS.FAIL, 901203)

    def _test_500(self):
        ''' 计划：添加计划500个 '''
        self._add(CampaignType.factory(500))

    def test_exceed(self):
        ''' 计划：添加计划，超过500个 '''
        server, user = self.server, self.user
        campaigns = CampaignType.factory(501)
        res = self.addCampaign(body=campaigns)
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
        res = self.addCampaign(body=CampaignType.random())
        self._original_campaign = res.body.campaignTypes[0]
        self.campaignId = self._original_campaign.campaignId

    def _update(self, **kwargs):
        ''' 计划：添加，并检查 '''
        server, user = self.server, self.user
        campaignId = kwargs.setdefault('campaignId', self.campaignId)
        # 原计划
        campaign = self.getCampaignByCampaignId(
            body=CampaignId(self.campaignId)
        ).body.campaignTypes[0]
        campaign = CampaignType(**campaign)
        # 更新计划
        update_campaign = CampaignType(**kwargs)
        res = self.updateCampaign(body=update_campaign)
        assert_header(res.header)
        # 查询数据库
        res = self.getCampaignByCampaignId(
            body=CampaignId(campaignId))
        # 对比
        base = res.body.campaignTypes[0]
        expect = campaign.normalize(update_campaign)
        assert expect == base, u'计划更新后不符合预期\n'\
            u'原来: %s\n更新: %s\n期望: %s\n实际: %s\n' % (
                campaign, kwargs, expect, base)

    def _expect_fail(self, code, **kwargs):
        '''
        验证错误，code是错误码，可以是数组
        '''
        kwargs.setdefault('campaignId', self.campaignId)
        res = self.updateCampaign(body=CampaignType(**kwargs))
        assert_header(res.header, STATUS.FAIL, code)

    def test_title01(self):
        """ 计划：更新计划名称为1个字符 """
        self._update(campaignName='1')

    def test_title02(self):
        """ 计划：更新计划名称为30个字符 """
        self._update(campaignName=gen_chinese_unicode(30))

    def test_title03(self):
        """ 计划：更新计划名称为31个字符，错误码901202 """
        self._expect_fail(901202, campaignName=gen_chinese_unicode(31))

    def test_title04(self):
        """ 计划：更新计划名称为相同的用户名，错误码901203 """
        self._expect_fail(
            901203, 
            campaignName=self._original_campaign.campaignName)

    def test_budget01(self):
        ''' 计划：更新计划预算为9.99, 错误码901232 '''
        self._expect_fail(901232, budget=9.99)

    def test_budget02(self):
        ''' 计划：更新计划预算为10.49, 测试精度 '''
        self._update(budget=10.49)
        self._update(budget=10.49435)

    def test_budget08(self):
        ''' 计划：更新计划预算为10.4959, 测试精度 '''
        self._update(budget=10.4959)

    def test_budget03(self):
        ''' 计划：更新计划预算为500000.00，正常更新 '''
        self._update(budget=500000.00)

    def test_budget04(self):
        ''' 计划：更新计划预算为500000.01, 错误码901233 '''
        self._expect_fail(901233, budget=500000.01)
        self._expect_fail(901233, budget='500000.01')

    def test_budget05(self):
        ''' 计划：更新计划预算为0，取消限制 '''
        self._update(budget=0)
        self._update(budget='0.00')

    def test_budget06(self):
        ''' 计划：更新计划预算为空串''
        空串''和null值不一样,null表示不修改，空串''应该改报错 '''
        self._expect_fail(None, budget='')

    def test_budget07(self):
        ''' 计划：更新计划预算为-1, 错误码901232 '''
        self._expect_fail(901232, budget=-1.0)
        self._expect_fail(901232, budget='-1')

    def test_default(self):
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

    def test_pause(self):
        ''' 计划：更新计划状态pause '''
        self._update(pause=True)
        # 默认不修改
        self._update(pause=None)
        self._update(pause=False)
        # 默认不修改
        self._update(pause=None)

    def test_region01(self):
        ''' 计划：更新计划，地域为'所有地域' '''
        self._update(
            campaignId=self.campaignId, regionTarget=[u'所有地域'])

    def test_region02(self):
        ''' 计划：更新计划，地域为'北京;江苏-南京' '''
        self._update(
            campaignId=self.campaignId, regionTarget=[u'北京',u'江苏-南京'])

    def test_region03(self):
        ''' 计划：更新计划，地域为'你好', 错误码901243 '''
        self._expect_fail(901243, regionTarget=[u'你好'])

    def test_region04(self):
        ''' 计划：更新计划，地域为'江苏;江苏-南京', 错误码901243 '''
        self._expect_fail(901243, regionTarget=[u'江苏', u'江苏-南京'])

    def test_region05(self):
        ''' 计划：更新计划，地域为'南京', 错误码901243 '''
        self._expect_fail(901243, regionTarget=[u'南京'])

    def test_region06(self):
        ''' 计划：更新计划，地域为空集[] '''
        self._update(
            campaignId=self.campaignId, regionTarget=[])

    def test_region07(self):
        ''' 计划：更新计划，地域为空串'', 错误码901243 '''
        server, user = self.server, self.user
        campaign = CampaignType(
            campaignId=self.campaignId, regionTarget=[''])
        res = self.updateCampaign(body=campaign)
        # 901203: 计划名称已存在
        assert_header(res.header, STATUS.FAIL, 901243)

    def test_excludeIp01(self):
        ''' 计划：更新计划的IP排除 '''
        self._update(excludeIp=['10.9.*.*', '42.120.172.*', '127.0.0.1'])

    def test_excludeIp02(self):
        ''' 计划：取消计划的IP排除限制 '''
        self._update(excludeIp=['$'])

    def test_negativeWords01(self):
        """ 计划：更新计划的否定关键词 """
        self._update(negativeWords=[u'否定01', u'否定02'])

    def test_negativeWords02(self):
        ''' 计划：更新计划，取消否定关键词限制 '''
        self._update(negativeWords=['$'])

    def test_exactNegativeWords01(self):
        """ 计划：更新计划的精确否定关键词 """
        self._update(exactNegativeWords=[u'精确否定', u'否定关键词'])

    def test_exactNegativeWords02(self):
        ''' 计划：更新计划，取消精确否定关键词限制 '''
        self._update(exactNegativeWords=['$'])

    def test_schedule01(self):
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

    def test_schedule02(self):
        """ 计划：更新计划的推广时段为空串'' """
        self._update(schedule='')

    def test_showProb(self):
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

if __name__ == '__main__':
    setup_env(api.campaign, server=ThreadLocal.SERVER, header=ThreadLocal.USER)
