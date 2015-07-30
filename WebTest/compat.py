#! -*- coding:utf8 -*-

from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException, ElementNotVisibleException)
from selenium.webdriver.common.by import By

######################################################################
#  不要交叉 import
#  decorate `WebElement.find_elements`


def displayed_dec(func):
    def wrapper(*args, **kwargs):
        items = func(*args, **kwargs)
        return filter(lambda x: x.is_displayed() and x.size['height'] * x.size['width'], items)
    return wrapper


def index_displayed(func):
    '''
    @return (index, WebElement)
    '''
    def wrapper(*args, **kwargs):
        items = func(*args, **kwargs)
        return filter(
            lambda (idx, x): x.is_displayed() and x.size[
                'height'] * x.size['width'],
            enumerate(items)
        )
    return wrapper
'''
借鉴requests的做法，封装所有需要的库
'''
if not hasattr(WebElement, '_find_elements'):
    WebElement._find_elements = WebElement.find_elements

WebElement.find_elements_with_index = index_displayed(
    WebElement._find_elements)

WebElement.find_elements = displayed_dec(WebElement._find_elements)

######################################################################
