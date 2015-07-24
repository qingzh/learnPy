#! -*- coding:utf8 -*-

from selenium.webdriver import PhantomJS

url = 'http://42.120.168.74'


def login(driver):
    driver.get(url)
    driver.find_element_by_xpath(
        '//input[@id="username"]').send_keys('ShenmaPM2.5')
    driver.find_element_by_xpath(
        '//input[@id="password"]').send_keys('pd123456')
    driver.find_element_by_xpath(
        '//input[@name="captchaResponse"]').send_keys('1')
    driver.find_element_by_xpath('//input[@name="submit"]').click()

'''
> js.get_cookies()
[{u'domain': u'42.120.168.71',
  u'httponly': True,
  u'name': u'JSESSIONID',
  u'path': u'/cpc/',
  u'secure': False,
  u'value': u'A34B9195A09623F2F2D82007D82C4164-n1'}]
'''


def prepare_driver(js):
    js = PhantomJS()
    login(js)
    # 进入推广管理
    js.get(url + '/cpc/adManagement')

from selenium.webdriver.common.by import By
from APITest.model.models import AttributeDict
import logging
from selenium.webdriver.remote.webelement import WebElement

log = logging.getLogger(__name__)


def displayed_dec(func):
    def wrapper(*args, **kwargs):
        print args, kwargs
        items = filter(lambda x: x.is_displayed(), func(*args, **kwargs))
        return filter(lambda x: x.size['height'] * x.size['width'], items)
    return wrapper

WebElement.find_elements = displayed_dec(WebElement.find_elements)


class ContainerMixin(object):

    @property
    def header(self):
        log.debug(self._elements_.header)
        return self.main.find_element(*self._elements_.header)

    @property
    def content(self):
        log.debug(self._elements_.content)
        return self.main.find_element(*self._elements_.content)


class TabPage(ContainerMixin):

    def __init__(self, driver):
        '''
        必须用driver初始化，如果用WebElement的话，可能会出错
        因为WebElement记录的是对象，是会变化的
        '''
        self.driver = driver
        self._elements_ = AttributeDict({
            'main': (By.XPATH, '//div[@class="main-nav head-tab"]'),
            'header': (By.CLASS_NAME, 'main-nav-title'),
            'content': (By.CLASS_NAME, 'main-nav-content'),
        })

    # 分N个主要框架
    # 主TAB页面0

    @property
    def main(self):
        log.debug(self._elements_.main)
        return self.driver.find_element(*self._elements_.main)

    def get_headers(self):
        return filter(lambda x: x.is_displayed(), self.header.find_elements(By.XPATH, './li'))

    def get_names(self):
        '''
        TAB页面的标签文本
        '''
        return map(lambda x: x.text, self.get_headers())

    def get_ids(self):
        '''
        TAB页面的标签id
        '''
        return map(lambda x: x.get_attribute('id'), self.get_headers())


class TabContent(ContainerMixin):

    def __init__(self, obj):
        # 单行操作列
        self.main = obj
        self._elements_ = AttributeDict({
            'header': (By.CLASS_NAME, 'main-nav-head'),
            'content': (By.CLASS_NAME, 'main-table-area'),
            'elements': (By.XPATH, './*/*[@class]')
        })

    @property
    def items(self):
        return self.header.find_elements(*self._elements_.elements)

    def get_names(self):
        return map(lambda x: x.text, self.items)
