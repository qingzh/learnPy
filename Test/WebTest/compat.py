#! -*- coding:utf8 -*-

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException, ElementNotVisibleException, WebDriverException)
from selenium.webdriver.common.by import By
import logging

######################################################################
#  不要交叉 import
#  decorate `WebElement.find_elements`

# TODO
# driver.find_element 也要检查是否加载完成
# 但是 WebElement.find_element 则不需要

# 线上环境最长等待时间：120 seconds
log = logging.getLogger(__name__)
MAX_WAIT_TIME = 180


def load_complete_dec(func):
    def wrapper(self, *args, **kwargs):
        ret = func(self, *args, **kwargs)
        try:
            el = self.parent.find_element_by_xpath(
                '//body/div[@id="windownbg"]')
            WebDriverWait(el, MAX_WAIT_TIME).until_not(
                lambda x: 'block' in x.get_attribute('style'))
        except Exception as e:
            log.info('load_complete_dec:', e)
        return ret
    return wrapper

_click = WebElement.click
WebElement.click = load_complete_dec(_click)


def driver_load_complete_dec(func):
    def wrapper(self, *args, **kwargs):
        ret = func(self, *args, **kwargs)
        try:
            el = self.find_element_by_xpath(
                '//body/div[@id="windownbg"]')
            WebDriverWait(el, MAX_WAIT_TIME).until_not(
                lambda x: 'block' in x.get_attribute('style'))
        except Exception as e:
            log.info('driver_load_complete_dec:', e)
        return ret
    return wrapper

_refresh = WebDriver.refresh
WebDriver.refresh = driver_load_complete_dec(_refresh)
_get = WebDriver.get
WebDriver.get = driver_load_complete_dec(_get)


def displayed_dec(func):
    def wrapper(self, by, locator, visible=True):
        items = func(self, by, locator)
        if visible is False:
            return items
        return filter(lambda x: x.is_displayed() and x.size[
            'height'] * x.size['width'], items)
    return wrapper


def index_displayed(func):
    '''
    @return (index, WebElement)
    '''

    def wrapper(self, by, locator, visible=True):
        items = func(self, by, locator)
        if visible is False:
            return list(enumerate(items))
        '''
        为什么需要显示 size > 0??
        x.is_displayed() and x.size['height'] * x.size['width']
        '''
        return filter(
            lambda (idx, x): x.is_displayed(), enumerate(items))
    return wrapper

'''
借鉴requests的做法，封装所有需要的库
'''
_find_elements = WebElement.find_elements
WebElement.find_elements_with_index = index_displayed(_find_elements)
WebElement.find_elements = displayed_dec(_find_elements)

######################################################################
