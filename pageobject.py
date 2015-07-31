#! -*- coding:utf8 -*-


from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import time
from selenium.common.exceptions import (
    NoSuchElementException, ElementNotVisibleException)
from selenium.webdriver.common.action_chains import ActionChains
from APITest.model.models import _slots_class
from WebTest.models.cpc import LoginPage, CPCPage
from WebTest.utils import _find_input, _set_input, gen_chinese_unicode
import random

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


def func(driver):
    cookies = {u'domain': u'e.sm.cn',
               u'expiry': None,
               u'httpOnly': True,
               u'name': u'JSESSIONID',
               u'path': u'/cpc/',
               u'secure': False,
               u'value': u'24FBD20936B60AB6B712197BC2DF73D3-n1'}
    driver.get('https://e.sm.cn')
    driver.add_cookie(cookies)
    driver.get('https://e.sm.cn/cpc/adManagement')
    return driver

from selenium.webdriver import Chrome
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

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


def test_main(driver):
    login(driver)
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
