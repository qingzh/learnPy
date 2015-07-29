#! -*- coding:utf8 -*-


from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import time
from selenium.common.exceptions import (
    NoSuchElementException, ElementNotVisibleException)
from selenium.webdriver.common.action_chains import ActionChains
from APITest.model.models import _slots_class
from WebTest.models.cpc import LoginPage, CPCPage
from WebTest.utils import _find_input, _set_input, displayed_dec, index_displayed

'''
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


######################################################################
#  decorate `WebElement.find_elements`

if not hasattr(WebElement, '_find_elements'):
    WebElement._find_elements = WebElement.find_elements

WebElement.find_elements_with_index = index_displayed(
    WebElement._find_elements)

WebElement.find_elements = displayed_dec(WebElement._find_elements)

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


url = 'http://42.120.168.74'


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
 u'value': u'FC3769042C63D37F9AD1BCD0F07A200B-n1'}
    driver.get('https://e.sm.cn')
    driver.add_cookie(cookies)
    driver.get('https://e.sm.cn/cpc/')
    return driver
