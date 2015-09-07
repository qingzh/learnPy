#! -*- coding:utf8 -*-

'''
/cpc/appSource

'''

from .common import *
from ..compat import By, WebElement
from ..utils import kwargs_dec
import collections


class HeaderContainer(BaseContainer):

    '''
    CPC系统页头，应该所有系统都是一致的？
    '''
    header = ContainerElement(
        By.XPATH, './/ul[@class="head-nav"]',
        DictContainer, subxpath='./li/a', subobj=InputElement)


# 选择日期


class DateContainer(BaseContainer):

    '''
    Date format: '2015-01-01'
    >>> date = DateContainer(parent, by, locator)
    >>> date.start_date = '2015-01-01'
    >>> date.header.get(u'本月').click()
    '''

    header = ContainerElement(
        By.XPATH, './/div[@class="fast-link"]', DictContainer)
    start_date = InputElement(By.CSS_SELECTOR, 'div.fn-date-left input')
    end_date = InputElement(By.CSS_SELECTOR, 'div.fn-date-right input')
    confirm = InputElement(By.CSS_SELECTOR, 'a.confirm-btn')
    cancel = InputElement(By.CSS_SELECTOR, 'a.close-btn')

    def set_date(self, start, end):
        self.start_date = start
        self.end_date = end
        self.confirm = True

    def set_header(self, value):
        self.header = value
        self.confirm = True

date_container = DateContainer(
    None, By.XPATH, '../div[@class="fn-date-container left"]')


class TRContainer(BaseContainer):
    # 存储单元格内容
    tr = ListElement(By.XPATH, './td', BaseElement)


class TableContainer(BaseContainer):
    title = ContainerElement(
        By.CSS_SELECTOR, 'div.table_head', BaseContainer)

    # 排序
    order = ContainerElement(
        By.XPATH, './/table',
        DictContainer(None, By.XPATH, './thead/tr', subxpath='.//span[contains(@class, "order")]',
                      subobj=kwargs_dec(
                          StatusElement,
                          key=lambda x: x.get_attribute(
                              'class').rpartition(' ')[-1],
                          key_map={u'升序': 'order-up', u'降序': 'order-down'}),
                      key=lambda x: x.find_element(By.XPATH, '..').text.strip()))

    thead = ContainerElement(
        By.XPATH, './/table/thead/tr', ListContainer, subxpath='./td', subobj=BaseElement)
    tbody = ContainerElement(
        By.CSS_SELECTOR, 'table.table > tbody', ListContainer, subxpath='./tr', subobj=TRContainer)

    page_index = InputElement(
        By.XPATH, '//div[@class="ad_page"]//li[@class="page-turn"]/span/input')
    page_confirm = InputElement(
        By.XPATH, '//div[@class="ad_page"]//li[@class="page-turn"]/a')

    def set_number(self, value):
        if value is None:
            return
        self.page_index = value
        self.page_confirm = True


class FormContainer(BaseContainer):
    date = ContainerElement(
        By.CSS_SELECTOR, 'div.fn-dates-picker div.input-append', date_container)
    level = ContainerElement(
        By.CSS_SELECTOR, 'div.level-radios',
        DictContainer, subxpath='./input', subobj=InputElement,
        key=lambda x: x.get_attribute('data-level'))
    dateType = ContainerElement(
        By.CSS_SELECTOR, 'div.date-radios',
        DictContainer, subxpath='./input', subobj=InputElement,
        key=lambda x: x.find_element(By.XPATH, './following-sibling::*').text.strip())
    dataMain = ContainerElement(
        By.CSS_SELECTOR, 'div.date-select',
        DictContainer, subxpath='./input', subobj=InputElement,
        key=lambda x: x.find_element(By.XPATH, './following-sibling::*').text.strip())
    confirm = InputElement(By.CSS_SELECTOR, 'div.fn-clear a.sub_btn')

    def set_date(self, start, end):
        self.date.set_date(start, end)

    def set_data(self, level=None, dateType=None, dataMain=None):
        if level:
            self.level = level
        if dateType:
            self.dateType = dateType
        if dataMain:
            self.dataMain = dataMain

    def submit(self):
        self.confirm = True


class AddPage(BaseContainer, dict):

    appName = InputElement(By.CSS_SELECTOR, 'input[name=appName]')
    versionName = InputElement(By.CSS_SELECTOR, 'input[name=versionName]')
    appShowName = InputElement(By.CSS_SELECTOR, 'input[name=appShowName]')
    appType = ContainerElement(
        By.CSS_SELECTOR, 'div[name=appType]',
        DictContainer, subxpath='.//input', subobj=InputElement,
        key=lambda x: x.find_element_by_xpath('..').text.strip())
    appName = InputElement(By.CSS_SELECTOR, 'input[name=appName]')
    appName = InputElement(By.CSS_SELECTOR, 'input[name=appName]')
    appName = InputElement(By.CSS_SELECTOR, 'input[name=appName]')
    appName = InputElement(By.CSS_SELECTOR, 'input[name=appName]')
    appName = InputElement(By.CSS_SELECTOR, 'input[name=appName]')


class appSource(BasePage):
    # 如果用ContainerElement
    # 则刷新页面之后，这个属性就废了！！！！

    # 如果在__init__初始化，就不能动态设置属性了！
    # self.header = ContainerElement(
    #     By.XPATH, '//body//div[@class="head"]', HeaderContainer)

    # 页头
    banner = ContainerElement(
        By.CSS_SELECTOR, 'body div.head', HeaderContainer)
    # 左侧树形图
    tree = ContainerElement(
        By.XPATH, '//body//div[@class="body-nav"]/ul',
        DictContainer, subxpath='./li', subobj=InputElement)
    # 中间主页面
    body = ContainerElement(
        By.CSS_SELECTOR, 'div.body-main-area', ReportContainer)
    add = ContainerElement(
        By.CSS_SELECTOR, 'form[name=appSubmitForm]', AddPage)
