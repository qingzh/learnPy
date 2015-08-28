#! -*- coding:utf8 -*-


from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import time
from selenium.common.exceptions import (
    NoSuchElementException, ElementNotVisibleException)
from selenium.webdriver.common.action_chains import ActionChains
from APITest.models.models import _slots_class, AttributeDict, SlotsDict
from WebTest.models.adTools import LoginPage, AdTools
from WebTest.utils import *
from WebTest.exceptions import *
import random
import logging
import threading
from requests.utils import unquote
import json
import urlparse
from selenium.webdriver import Chrome, Firefox
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


'''
######################################################################

TODO:
   还有一个问题就是，单击之后的寻址是正常的。
   但是 loading 页面的时候，都是不可点击的。
   所以要重写click事件，等待页面加载完成

######################################################################

self.parent: 控件的逻辑父节点
self.root: 控件的根节点，可能和self.parent相同

比如： 如果单击 AButton 触发控件 AContainer
    则 AButton 是 控件AContainer的逻辑父节点(.parent)
    而 AContainer 控件的根节点为 AContainer.root

我们需要一个 类似 _slots_class 的动态类
  _property_class 来动态生成Container

TODO:
    等待页面加载结束

改写 find_element 还是 改写 .click() .send_keys()


'''

INPUT_TEXT_TYPES = set(('text', 'password'))

PageInfo = _slots_class(
    'PageInfo', ('currentPage', 'level', 'totalPage', 'totalRecord', 'pageIndex'))

######################################################################


# 状态筛选窗口，这是全局唯一的控件
"""
计划
{
    计划暂停
    显示全部
    推广计划预算不足
    暂停时段
    推广中
    推广账户预算不足
}
assert .keys() == 以上 >,<...
"""


url = 'http://42.120.172.21/'


def login(driver, username='ShenmaPM2.5', password='pd123456'):
    driver.get(url)
    page = LoginPage(driver)
    page.username = username
    page.password = password
    page.captcha = '1'
    page.submit = True
    return driver

'''
def quit(driver):
    element = driver.find_element(By.LINK_TEXT, u'退出')
    element.click()
'''


def _show_all(page):
    page.tab.header.row_title.header[u'全部'] = True


def _batch_resume(page):
    page.tab.batch.resume = None
    alert = page.parent.switch_to_alert()
    expected = u'是否确认恢复所有选中的'
    assert alert.text.startswith(expected), u'Text not matched!\nExpected: "%s"\nActual: "%s"' % (
        expected, alert.text)
    alert.accept()


def batch_resume(driver):
    page = CPCPage(driver).body.tab
    # Choose Single Page
    page.table.header.checkbox = True
    _batch_resume(page)

    time.sleep(3)
    # Choose Multi Page
    if len(page.numbers) > 1:
        page.table.header.checkbox = True
        page.allRecords = True
        _batch_resume(page)


def add_cookie(driver):
    cookies = []
    driver.get('https://e.sm.cn/cpc')
    map(lambda x: driver.add_cookie(x), cookies)
    driver.get('https://e.sm.cn/cpc')
    return driver


######################################################################
#  Crhome Options
#  获取 performance logging
#  或者 cr.execute_script('return window.performance.getEntries().slice(i)')
#       @param i: index of the first element,
#       @return [i:]

caps = DesiredCapabilities.CHROME
caps['loggingPrefs'] = {'performance': 'ALL'}
# cr = Chrome(desired_capabilities=caps)

######################################################################


def test_cpc_main(driver, **kwargs):
    login(driver, **kwargs)
    cpc = CPCPage(driver)
    # 进入推广管理
    time.sleep(3)
    cpc.banner.header = u'推广管理'
    time.sleep(3)
    # 测试 Tab 页面
    tab = cpc.body.main
    tab.level = u'计划'
    return driver


def edit_single(driver):
    page = CPCPage(driver)
    main = page.body.main
    main.level = u'单元'
    time.sleep(3)
    # 显示所有列
    main.tools.row_title.select_all()
    # 测试可编辑列
    tbody = main.table.tbody
    element = random.choice(tbody)
    # 编辑名字
    name = gen_chinese_unicode(30)
    element.name_editor.set_and_confirm(name)
    assert element.unitName.text == name

######################################################################
#  Capture Tiem delta with `Crhome`
# caps['loggingPrefs'] = {'performance': 'ALL'}
# cr = Chrome(desired_capabilities=caps)


TIME_LOGGER = logging.getLogger('time-delta')
TIMEINFO = TIME_LOGGER.info


class PerformanceEntry(SlotsDict):
    _parsed = None
    _parsed_query = None
    __slots__ = ['secureConnectionStart',
                 'redirectStart',
                 'redirectEnd',
                 'name',
                 'startTime',
                 'domainLookupEnd',
                 'connectEnd',
                 'requestStart',
                 'initiatorType',
                 'responseEnd',
                 'fetchStart',
                 'duration',
                 'responseStart',
                 'entryType',
                 'connectStart',
                 'domainLookupStart',
                 '_parsed',
                 '_parsed_query']

    def __init__(self, *args, **kwargs):
        # TODO: not compatible with nested dict
        super(SlotsDict, self).__init__(*args, **kwargs)

    def __hash__(self):
        return hash(tuple(self.values()))

    @property
    def processingTime(self):
        return self.responseStart - self.requestStart

    @property
    def parsed(self):
        if self._parsed is None:
            self._parsed = urlparse.urlparse(self.name)
        return self._parsed

    @property
    def parsed_query(self):
        if self._parsed_query is None:
            self._parsed_query = AttributeDict(
                urlparse.parse_qs(self.parsed.query))
        return self._parsed_query


def time_delta_list(driver, initiatorType="xmlhttprequest"):
    # Get array of performance entry
    # 只要不刷新页面，就能一直保留
    t = driver.execute_script(
        '''return window.performance.getEntriesByType("resource").filter(
            function(x){
                return x.initiatorType.toLowerCase() == "%s";
            })''' % initiatorType.lower())
    return map(lambda x: PerformanceEntry(x), t)


def time_delta(driver, pattern=r'.json'):
    # Get array of performance entry
    item = driver.execute_script(
        '''return window.performance.getEntriesByType("resource").filter(function(x){
            return x.name.match(/%s/);
        }).pop()''' % pattern)
    if item:
        log.debug(
            '%15.5f | %15.5f', item['requestStart'], item['responseStart'])
        log.debug('Performance Length: %s', driver.execute_script(
            'return window.performance.getEntries().length'))
        return PerformanceEntry(item)
    print 'Performance getEntries:', item
    return None  # or raise Exception


def get_page_info(driver, attr=None):
    page_info = PageInfo(driver.execute_script('return pageArea.getData()'))
    if attr is None:
        return page_info
    return page_info[attr]


def clear_performance_timing(driver):
    performance.extend(driver.execute_script(
        'return window.performance.getEntriesByType("resource")'))
    driver.execute_script('window.performance.webkitClearResourceTimings()')
    driver.execute_script(
        'window.performance.webkitSetResourceTimingBufferSize(300)')


record_dict = {}


class TimeRecord(object):

    def __init__(level, status, totalRecord, pageNum, orderName=None, orderValue=None):
        self.status = status
        self.pageNum = pageNum
        self.totalRecord = totalRecord
        self.orderName = orderName
        self.orderValue = orderValue


class PageArea(AttributeDict):

    '''
    pa = PageArea(**driver.execute_script('return pageArea.getData()'))
    '''

    def __init__(self, currentPage=None, totalPage=None, totalRecord=None, level=None, pageIndex=None):
        self.currentPage = currentPage
        self.totalPage = totalPage
        self.totalRecord = totalRecord
        self.level = level
        self.pageIndex = pageIndex

    def random_turn(self):
        if self.totalPage > 1:
            return random.randint(2, self.totalPage)
        return None
######################################################################
#  Capture Network Traffic
#  Start the browser in "proxy-injection mode"
#   http://stackoverflow.com/questions/3712278/selenium-rc-how-do-you-use-capturenetworktraffic-in-python
# https://groups.google.com/forum/#!topic/selenium-users/v7rdTChQkbM

"""
from selenium import webdriver
from selenium.webdriver.common.proxy import *

myProxy = "host:8080"

proxy = Proxy({
    'proxyType': ProxyType.MANUAL,
    'httpProxy': myProxy,
    'ftpProxy': myProxy,
    'sslProxy': myProxy,
    'noProxy': ''  # set this value as desired
})

driver = webdriver.Firefox(proxy=proxy)

# for remote
caps = webdriver.DesiredCapabilities.FIREFOX.copy()
proxy.add_to_capabilities(caps)

driver = webdriver.Remote(desired_capabilities=caps)
"""
######################################################################

import requests
from requests import cookies


def set_session_cookies_from_driver(session, driver):
    for cookie in driver.get_cookies():
        if 'expiry' in cookie:
            cookie['expires'] = cookie.pop('expiry')
        session.cookies.set_cookie(cookies.create_cookie(**cookie))

'''
使用session.get('http://e.sm.cn/cpc/adManagement?uid=1061') 失败
但是requests.get('http://e.sm.cn/cpc/adManagement?uid=1061', cookies = session.cookies) 成功
'''

entries = {}
REPORT_LEVEL = (
    u"账户报告",
    u"计划报告",
    u"单元报告",
    u"关键词报告",
    u"创意报告",
    u"蹊径报告",
    u"电话报告",
    u"APP报告",
    u"无效点击报告",
    u"分地域报告",
)
REPORT_LEVEL = (
    u"关键词报告",
    u"创意报告",
)

DATE_TYPE = (u'分日', u'分月', u'汇总')

performance = []


def test_adTools(driver):
    driver.refresh()
    page = AdTools(driver)

    def do_record(o):
        pa = PageArea(
            **driver.execute_script('return pageArea.getData()'))
        record = entries.setdefault(level, {}).setdefault(
            dateType, {})
        record['total'] = pa.totalRecord
        record.setdefault(order, {}).setdefault(
            o, []).append((pa.currentPage, time_delta(driver, 'report')))

        print level, dateType, order, o, pa.totalRecord, record[order][o][-1][-1].processingTime

        index = pa.random_turn()
        print level, dateType, order, o, index
        if index is None:
            record[order][o].append(
                (0, PerformanceEntry(responseStart=0, requestStart=0)))
            return

        table.set_number(index)
        record[order][o].append((index, time_delta(driver, 'report')))

        pa_after = PageArea(
            **driver.execute_script('return pageArea.getData()'))
        assert pa_after.totalRecord == pa.totalRecord
        assert pa_after.totalPage == pa.totalPage

    form = page.body.form
    form.set_date('2015-06-25', '2015-08-05')

    for level, dateType in ((u'关键词报告', u'汇总'), (u'创意报告', u'分日')):
        clear_performance_timing(driver)
        form.set_data(level, dateType)
        form.submit()
        table = page.body.table
        for order in table.order.keys():
            table.order[order] = u'降序'
            do_record(u'降序')

            table.order[order] = u'升序'
            do_record(u'升序')

    return
    for level in REPORT_LEVEL:
        date_list = form.dateType.keys()
        for dateType in (x for x in DATE_TYPE if x in date_list):
            clear_performance_timing(driver)
            form.set_data(level, dateType)
            form.submit()
            table = page.body.table
            for order in table.order.keys():
                table.order[order] = u'降序'
                do_record(u'降序')

                table.order[order] = u'升序'
                do_record(u'升序')


def format(d):
    for i in REPORT_LEVEL:
        if i == u'无效点击报告':
            continue
        d0 = d[i]
        for j in [u'分日', u'分月', u'汇总']:
            if j not in d0:
                continue
            d1 = d0[j]
            print '%s,%s,%s,' % (i, j, d1['total']),
            for k in [u'展现量', u'点击量', u'消费', u'点击率',  u'平均点击价格']:
                if k not in d1:
                    continue
                d2 = d1[k]
                sx = d2[u'升序']
                jx = d2[u'降序']
                print '%.5f,%.5f,%.5f,%.5f,' % (
                    sx[0][-1].processingTime, sx[1][-1].processingTime,
                    jx[0][-1].processingTime, jx[1][-1].processingTime),
            print
    i = u'无效点击报告'
    d0 = d[i]
    for j in [u'分日', u'分月', u'汇总']:
        d1 = d0[j]
        print '%s,%s,%s,' % (i, j, d1['total']),
        for k in [u'过滤金额', u'过滤前点击量', u'过滤点击量']:
            d2 = d1[k]
            sx = d2[u'升序']
            jx = d2[u'降序']
            print '%.2f,%.2f,%.2f,%.2f,' % (sx[0][-1].processingTime, sx[1][-1].processingTime, jx[0][-1].processingTime, jx[1][-1].processingTime),
        print


def test_main(uid=1061):
    cr = Chrome('./chromedriver', desired_capabilities=caps)
    try:
        login(cr, 'smdev', 'smdevsmdev')
    except Exception:
        pass
    cr.get(url + '/cpc/adTools?uid=%s' % uid)
    cr.maximize_window()
    test_adTools(cr)

if __name__ == '__main__':
    # test_main(1061)
    pass


# ---------------------------------------------------
from WebTest.models.common import log as web_log
from TestCommon.models.const import STDOUT
web_log.setLevel(logging.DEBUG)
# web_log.addHandler(STDOUT)
