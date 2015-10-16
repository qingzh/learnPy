# -*- coding:utf-8 -*-
'''
针对 账户(Account) 接口的回归测试:
'''

from APITest.models.account import *
from APITest.settings import api, SQL
from APITest.utils import assert_header, get_log_filename
from APITest import (
    TestCase, formatter, ThreadLocal, log_dec, BLANK)
from APITest import API_STATUS as STATUS
import logging
from functools  import partial
import pymysql as db

##########################################################################
#    log settings

TAG_TYPE = u'ACCOUNT'
LOG_FILENAME = get_log_filename(TAG_TYPE)

__loglevel__ = logging.DEBUG
log = logging.getLogger(__name__)
log.setLevel(__loglevel__)

##########################################################################
SERVER = ThreadLocal.SERVER
USER = ThreadLocal.USER


'''
"account": {
    "self.getAccount": APIRequest(method=post, uri='/api/account/self.getAccount'),
    "self.updateAccount": APIRequest(method=post, uri='/api/account/self.updateAccount'),
}
'''
env = locals()

def setup_env(source, **kwargs):
    for key, value in source.items():
        env[key] = partial(value, **kwargs)

# ------------------------------------------------------------------------
# 准备测试数据
# description 总长
# 字典里存的是json形式，因为list不能hash
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------

class MySQL(object):
    ''' 这里没有关闭数据库 '''
    def __init__(self, **kwargs):
        try:
            conn = self.conn = db.connect(**kwargs)
        except Exception:
            self.conn = BLANK

    def execute(self, s):
        if self.conn is BLANK:
            return BLANK
        cur = self.conn.cursor()
        amount = cur.execute(s)
        if amount == 1:
            ret = cur.fetchone()
        else:
            ret = cur.fetchall()
        cur.close()
        return ret


class AccountMixin(TestCase):

    '''
    需要进行配置吗？WHY?
    预算：2015.49
    地域：江苏-南京; 上海
    排除IP：127.0.0.1; 0.0.*.*
    '''
    def setup_env(self, source):
        for key, value in source.items():
            self.__dict__[key] = partial(
                value, server=self.server, header=self.user)

    def __init__(self, server=None, user=None, uid=None):
        super(AccountMixin, self).__init__()
        self.server = server or ThreadLocal.SERVER
        self.user = user or ThreadLocal.user
        self.setup_env(api.account)

        # 配置服务器
        self.sql = MySQL(**SQL)

        if uid:
            self.uid = uid
        else:
            pass
            # self.uid = get_uid(user['username'])
        self._default_accountInfo = AccountType(
            budgetType=1,
            budget='2015.49',
            regionTarget=[u'江苏-南京', u'上海'],
            excludeIp=['127.0.0.1', '0.0.*.*'])

    def setUp(self):
        '''
        应当转化为数据库操作
        '''
        server, user = self.server, self.user
        # response.body: {'campaignIds':[...]}
        accountInfo = self.getAccount(
            body=GETACCOUNT).body.accountInfoType
        '''
        如果excludeIp 为空(返回值是 [''] )
        则将excludeIp 做一个转义 (转义成['$'])
        '''
        excludeIp = accountInfo.excludeIp
        if excludeIp == ['']:
            excludeIp = ['$']
        self._original_accountInfo = AccountType(
            budget=accountInfo.budget,
            budgetType=accountInfo.budgetType,
            regionTarget=accountInfo.regionTarget,
            excludeIp=excludeIp)
        res = self.updateAccount(body=self._default_accountInfo)
        assert_header(res.header)

    def tearDown(self):
        server, user = self.server, self.user
        res = self.updateAccount(body=self._original_accountInfo)
        assert_header(res.header)


class UpdateAccount(AccountMixin):

    def _update(self, **kwargs):
        '''
        验证正面case，返回结果应该是 'success'
        '''
        server, user = self.server, self.user
        account = AccountType(**kwargs)
        res = self.updateAccount(body=account)
        assert_header(res.header)

        base = AccountType(**self.getAccount(
            body=GETACCOUNT).body.accountInfoType)
        expect = base.normalize(account)
        assert base == expect, 'Expected: {}\nActually: {}'.format(
            expect, base)

    def _expect_fail(self, code, **kwargs):
        '''
        验证负面case，返回结果应该是 'fail' + 错误码
        '''
        server, user = self.server, self.user
        res = self.updateAccount(body=AccountType(**kwargs))
        assert_header(res.header, STATUS.FAIL, code)

    def test_budget01(self):
        ''' 账户：更新预算类型为0(不限制)，预算为200，最后应该都为0 '''
        self._update(budgetType=0, budget=200)

    def test_budget02(self):
        ''' 账户：更新预算限制为10.59，测试精度 '''
        self._update(budgetType=1, budget=10.59)
        self._update(budgetType=1, budget='10.59')

    def test_budget03(self):
        ''' 账户：更新预算类型为0.13，错误码901155 '''
        self._expect_fail(901155, budgetType=0.13, budget=200)

    def test_budget04(self):
        ''' 账户：更新预算类型为'abc'，错误码800 '''
        self._expect_fail(800, budgetType='abc', budget=200)

    def test_budget05(self):
        ''' 账户：更新预算类型为-1，错误码901155 '''
        self._expect_fail(901155, budgetType=-1, budget=200)

    def test_budget06(self):
        ''' 账户：更新预算类型为3，错误码901155 '''
        self._expect_fail(901155, budgetType=3, budget=200)

    def test_budget07(self):
        ''' 账户：更新预算限制为10，测试精度 '''
        self._update(budgetType=1, budget=10)
        self._update(budgetType=1, budget='10.00')

    def test_budget08(self):
        ''' 账户：更新预算限制为9.99，错误码901152 '''
        self._expect_fail(901152, budgetType=1, budget=9.99)
        self._expect_fail(901152, budgetType=1, budget='9.99')

    def test_budget09(self):
        ''' 账户：更新预算限制为500000.01，错误码901153 '''
        self._expect_fail(901153, budgetType=1, budget=500000.01)
        self._expect_fail(901153, budgetType=1, budget='500000.01')

    def test_budget10(self):
        ''' 账户：更新预算限制为空串'', 错误码 901154 '''
        self._expect_fail(901154, budgetType=1, budget='')

    def test_budget11(self):
        ''' 账户：更新预算限制为-1, 错误码 901152 '''
        self._expect_fail(901152, budgetType=1, budget=-1)
        self._expect_fail(901152, budgetType=1, budget='-1')

    def test_budget12(self):
        ''' 账户：更新预算类型为空串'', 错误码 901155
        空串''和null值不一样,null表示不修改，空串''应该改报错 '''
        self._expect_fail(901155, budgetType='', budget='')

    def test_blank(self):
        ''' 账户：更新操作(不更新任何值) '''
        self._update()

    def test_null(self):
        ''' 账户：使用null值更新账户 '''
        self._update(
            budgetType=None,
            budget=None,
            regionTarget=None,
            excludeIp=None)

    def test_region01(self):
        ''' 账户：更新推广地域为'所有地域' '''
        self._update(regionTarget=[u'所有地域'])

    def test_region02(self):
        ''' 账户：更新推广地域为空集[]
        空集[]和null也是两个概念，空集[]表示投放地域一个也不选 '''
        self._update(regionTarget=[])

    def test_region03(self):
        ''' 账户：更新推广地域为'你好', 错误码901142 '''
        self._expect_fail(901142, regionTarget=[u'你好'])

    def test_region04(self):
        ''' 账户：更新推广地域为'江苏;江苏-南京', 错误码901142 '''
        self._expect_fail(901142, regionTarget=[u'江苏', u'江苏-南京'])

    def test_region05(self):
        ''' 账户：更新推广地域为'南京', 错误码901142 '''
        self._expect_fail(901142, regionTarget=[u'南京'])

    def test_region06(self):
        ''' 账户：更新推广地域为'北京;江苏-南京' '''
        self._update(regionTarget=[u'北京', u'江苏-南京'])

    def test_excludeIp01(self):
        ''' 计划：更新排除IP为 '1.1.1.*;1.1.*.*;127.0.0.1;0.0.0.0' '''
        self._update(
            excludeIp=['1.1.1.*', '1.1.*.*', '127.0.0.1', '0.0.0.0'])

    def test_excludeIp02(self):
        ''' 计划：更新排除IP为 '1.1.1.*;127.0.0.1;1.1.1.*;127.0.0.1;'
        自动去重 '''
        self._update(
            excludeIp=['1.1.1.*', '127.0.0.1', '1.1.1.*', '127.0.0.1'])

    def test_excludeIp03(self):
        ''' 计划：更新排除IP为 '1.2.3.4.5' '''
        self._expect_fail(901134, excludeIp=['1.2.3.4.5'])

    def test_excludeIp04(self):
        ''' 计划：更新排除IP为 '1.2.3.' '''
        self._expect_fail(901134, excludeIp=['1.2.3.'])

    def test_excludeIp05(self):
        ''' 计划：更新排除IP为 '1.*.*.*' '''
        self._expect_fail(901134, excludeIp=['1.*.*.*'])

    def test_excludeIp06(self):
        ''' 计划：更新排除IP为 '1.1.*.1' '''
        self._expect_fail(901134, excludeIp=['1.1.*.1'])

    def test_excludeIp07(self):
        ''' 计划：更新排除IP为 '1.0.0.256' '''
        self._expect_fail(901134, excludeIp=['1.0.0.256'])

    def test_excludeIp08(self):
        ''' 计划：更新排除IP为 '*' '''
        self._expect_fail(901134, excludeIp=['*'])


# ------------------------------------------------------------------------
#  测试入口
# ------------------------------------------------------------------------

@log_dec(log, LOG_FILENAME, __loglevel__)
def test_main(server=None, user=None, recover=True):
    server = server or ThreadLocal.SERVER
    user = user or ThreadLocal.USER
    UpdateAccount(server, user).run()

if __name__ == '__main__':
    setup_env(api.account, server=ThreadLocal.SERVER, header=ThreadLocal.USER)
