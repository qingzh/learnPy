#! -*- coding:utf8 -*-


from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import time
from selenium.common.exceptions import (
    NoSuchElementException, ElementNotVisibleException)
from selenium.webdriver.common.action_chains import ActionChains
from APITest.model.models import _slots_class, AttributeDict, SlotsDict
from WebTest.models.cpc import LoginPage, CPCPage
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
    'PageInfo', ('currentPage', 'level', 'totalPage', 'totalRecord'))

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


url = 'http://42.120.168.65/'


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
    cookies = [{u'domain': u'e.sm.cn',
                u'name': u'JSESSIONID',
                u'path': u'/cpc/',
                u'secure': False,
                u'value': u'5632AE823F921DF652E51169AFBE4630-n1'},
               {u'domain': u'e.sm.cn',
                u'name': u'JSESSIONID',
                u'path': u'/fs/',
                u'secure': False,
                u'value': u'D8D0C042D91A905E05FC5D8F98A3BBB2'},
               {u'domain': u'e.sm.cn',
                u'name': u'JSESSIONID',
                u'path': u'/message/',
                u'secure': False,
                u'value': u'F96E462644C5E8CEE38AE223402A1339'},
               {u'domain': u'e.sm.cn',
                u'name': u'JSESSIONID',
                u'path': u'/kr/',
                u'secure': False,
                u'value': u'81A103B140D39FA92A89790CD33AA886'},
               {u'domain': u'e.sm.cn',
                u'name': u'JSESSIONID',
                u'path': u'/report/',
                u'secure': False,
                u'value': u'77684926972F460CD239EC616879154F'},
               {u'domain': u'e.sm.cn',
                u'name': u'JSESSIONID',
                u'path': u'/oplog/',
                u'secure': False,
                u'value': u'8502C6403AB09647F98356C80918CFA0'}]
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


def test_main(driver, **kwargs):
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
        return PerformanceEntry(item)
    return None  # or raise Exception


def get_time_by_level(driver, level):
    page = CPCPage(driver)
    main = page.body.main
    main.level = level

    # 让所有控件可见，展示所有列，日期为上月
    driver.set_window_size(1600, 1200)
    main.tools.row_title.select_all()
    main.tools.date_picker.set_date('2015-06-01', '2015-07-01')

    def get_time_delta():
        pass

    # 开始记录时间啦啦啦啦
    _time_delta = kwargs_dec(time_delta, pattern=r'customizedList.json')
    entries = []
    table = main.table
    for _status in main.tools.status.keys():
        print '-' * 80, '\n', _status
        main.tools.status = _status
        entries.append((_time_delta(driver), _status, u'默认排序'))
        for _order in table.thead.order.keys():
            print _order
            # 默认是降序在前
            table.thead.order[_order] = u'降序'
            entries.append((_time_delta(driver), _status, _order, u'降序'))
            table.thead.order[_order] = u'升序'
            entries.append((_time_delta(driver), _status, _order, u'升序'))
        # 需要去掉过滤状态
        main.level = level

    return entries

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
