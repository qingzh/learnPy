%run test#! -*- coding:utf8 -*-

from .common import *
from ..compat import By, AttributeDict, is_sequence
import json
from functools import partial
from collections import Mapping


class Where(AttributeDict):

    def __init__(self, uid, where):
        self.uid = uid
        self.where = where

    @property
    def where(self):
        return self['where']

    @where.setter
    def where(self, value):
        if not isinstance(value, basestring):
            value = json.dumps(value)
        self['where'] = value


class HeaderContainer(BaseContainer):

    '''
    CPC系统页头，应该所有系统都是一致的？
    '''
    header = ContainerElement(
        By.XPATH, './/ul[@class="head-nav"]',
        DictContainer, subxpath='./li/a', subobj=InputElement)


class DateContainer(BaseContainer):

    '''
    Date format: '2015-01-01'
    >>> date = DateContainer(parent, by, locator)
    >>> date.start_date = '2015-01-01'
    >>> date.header.get(u'本月').click()
    '''

    header = ContainerElement(
        By.XPATH, './/div[@class="fast-link"]', DictContainer)
    startDate = InputElement(By.CSS_SELECTOR, 'div.fn-date-left input')
    endDate = InputElement(By.CSS_SELECTOR, 'div.fn-date-right input')
    confirm = InputElement(By.CSS_SELECTOR, 'a.confirm-btn')
    cancel = InputElement(By.CSS_SELECTOR, 'a.close-btn')

    def set_date(self, start, end):
        self.startDate = start
        self.endDate = end
        self.confirm = True

    def set_header(self, value):
        self.header = value
        self.confirm = True

    def __set__(self, obj, value):
        '''
        可以直接调用，比如:
        page.date = (date(2015,5,1), date(2015,6,1))
        '''
        self.parent = obj
        if is_sequence(value):
            self.set_date(*value)
        if isinstance(value, Mapping):
            self.set_date(**value)
        if isinstance(value, basestring):
            self.set_header(value)


date_container = DateContainer(
    None, By.XPATH, '../div[@class="fn-date-container left"]')


class TRContainer(BaseContainer):
    # 存储单元格内容
    tr = ListElement(By.XPATH, './td', BaseElement)


class TableContainer(BaseTableContainer):

    title = ContainerElement(
        By.CSS_SELECTOR, 'div.table_head', BaseContainer)

    # 排序
    order = ContainerElement(
        By.XPATH, './/table',
        DictContainer(
            None, By.XPATH, './thead/tr',
            subxpath='.//span[contains(@class, "order")]',
            subobj=partial(
                StatusElement,
                key=lambda x: x.get_attribute('class').rpartition(' ')[-1],
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

    def set_order(self, order, value):
        self.order[order] = value


class FormContainer(BaseContainer):
    _ordered_key = ('date', 'level', 'dateType', 'dataMain', 'confirm')

    date = ContainerElement(
        By.CSS_SELECTOR, 'div.fn-dates-picker div.input-append', date_container)
    level = ContainerElement(
        By.CSS_SELECTOR, 'div.level-radios',
        DictContainer, subxpath='./input', subobj=InputElement,
        key=lambda x: x.find_element(By.XPATH, './following-sibling::span').text.strip())
    dateType = ContainerElement(
        By.CSS_SELECTOR, 'div.date-radios',
        DictContainer, subxpath='./input', subobj=InputElement,
        key=lambda x: x.find_element(By.XPATH, './following-sibling::span').text.strip())
    dataMain = ContainerElement(
        By.CSS_SELECTOR, 'div.date-select',
        DictContainer, subxpath='./input', subobj=InputElement,
        key=lambda x: x.find_element(By.XPATH, './following-sibling::span').text.strip())
    confirm = InputElement(By.CSS_SELECTOR, 'div.fn-clear a.sub_btn')

    def set_date(self, start, end):
        self.date.set_date(start, end)

    def submit(self):
        self.confirm = True


class ReportContainer(BaseContainer):
    form = ContainerElement(
        By.CSS_SELECTOR, 'div.ad_form', FormContainer)
    table = ContainerElement(
        By.CSS_SELECTOR, 'div.ad_list', TableContainer)


class AdTools(BasePage):
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
