#! -*- coding:utf8 -*-

# 希望这里的WebElement是修改以后的

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
import logging
import random
from TestCommon.utils import (
    gen_chinese_unicode, gen_random_ascii, len_unicode, prepare_url)
from functools import update_wrapper

__all__ = ['_find_input', '_set_input', '_find_and_set_input',
           'len_unicode', 'gen_random_ascii', 'gen_chinese_unicode',
           'WebElement', 'WebDriver']

######################################################################
#  不要交叉 import
#  decorate `WebElement.find_elements`

# TODO
# driver.find_element 也要检查是否加载完成
# 但是 WebElement.find_element 则不需要

# 线上环境最长等待时间：120 seconds


'''

from selenium.webdriver.remote.webdriver import WebDriver
WebDriver.abc = 'haha'

__all__ = ['WebDriver']

----

即使只引入 WebDriver, 意即: import WebDriver
之后再引入 selenium, 意即：import selenium
此时：
selenium.webdriver.remote.webdriver.WebDriver 也会是新的WebDriver

因为 selenium.webdriver.remote.webdriver.WebDriver 和 webdriver 对象地址一样
* 我们只修改了对象属性，并没有修改对象本身 *

'''


log = logging.getLogger(__name__)

MAX_WAIT_TIME = 180


def load_complete_dec(func):
    '''
    等待页面加载完毕
    '''

    def wrapper(self, *args, **kwargs):
        ret = func(self, *args, **kwargs)
        try:
            driver = self.parent if isinstance(self, WebElement) else self
            el = driver.find_element_by_xpath('//body/div[@id="windownbg"]')
            WebDriverWait(el, MAX_WAIT_TIME).until_not(
                lambda x: 'block' in x.get_attribute('style'))
        except Exception as e:
            # 找不到 windownbg
            # 加载超时
            log.warn('[WARN] Loading page encounter: \n%s', e)
        return ret
    return update_wrapper(wrapper, func)

_click = WebElement.click
WebElement.click = load_complete_dec(_click)


def driver_get_dec(func):
    def wrapper(self, url):
        func(self, prepare_url(url))
    return update_wrapper(wrapper, func)

_default_refresh = WebDriver.refresh
WebDriver.refresh = load_complete_dec(_default_refresh)

_default_get = WebDriver.get
WebDriver.get = load_complete_dec(driver_get_dec(_default_get))


def displayed_dec(func):
    def wrapper(self, by, value, visible=True):
        items = func(self, by, value)
        if visible is False:
            return items
        return filter(lambda x: x.is_displayed() and x.size[
            'height'] * x.size['width'], items)
    return update_wrapper(wrapper, func)


def index_displayed(func):
    '''
    @return (index, WebElement)
    '''

    def wrapper(self, by, value, visible=True):
        items = func(self, by, value)
        if visible is False:
            return list(enumerate(items))
        '''
        为什么需要显示 size > 0??
        x.is_displayed() and x.size['height'] * x.size['width']
        '''
        return filter(
            lambda (idx, x): x.is_displayed(), enumerate(items))
    return update_wrapper(wrapper, func)

'''
借鉴requests的做法，封装所有需要的库
'''
_find_elements = WebElement.find_elements
WebElement.find_elements_with_index = index_displayed(_find_elements)
WebElement.find_elements = displayed_dec(_find_elements)

######################################################################

INPUT_TEXT_TYPES = set(('text', 'password'))

# 选择日期

'''
# 不需要，只需要在 InputElement 里，把 value 转换成 字符串 or 布尔
def set_date_wraps(cls):
    def __date_set__(self, obj, value):
        if not isinstance(value, basestring):
            value = str(value)
        super(cls, obj).__set__(obj, value)
    return __date_set__
'''


def _find_input(element):
    '''
    find input except `readonly` input
    @param element: Should be instance of WebElement
    '''
    if not isinstance(element, WebElement):
        raise TypeError('Expected WebElement!')
    if element.tag_name == 'input':
        return element
    _inputs = element.find_elements_by_xpath('.//input[not(@readonly)]')
    if not _inputs:
        return None
    if len(_inputs) == 1:
        return _inputs[0]
    raise Exception("Too many input!")


def _set_input(element, value):
    '''
    @param element: Should be instance of WebElement
    @param value
    '''
    if not isinstance(element, WebElement):
        raise TypeError('Expected WebElement!')
    if element.get_attribute('type') in INPUT_TEXT_TYPES:
        element.clear()
        element.send_keys(value)
    else:
        if value != element.is_selected():
            element.click()


def _find_and_set_input(element, value):
    '''
    @param element: Should be instance of WebElement
    '''
    if not isinstance(element, WebElement):
        raise TypeError('Expected WebElement!')
    _input = _find_input(element) or element
    _set_input(_input, value)


def get_random_unicode(length, unicode=False):

    try:
        get_char = unichr
    except NameError:
        get_char = chr

    # Update this to include code point ranges to be sampled
    include_ranges = [
        (0x0021, 0x0021),
        (0x0023, 0x0026),
        (0x0028, 0x007E),
        (0x00A1, 0x00AC),
        (0x00AE, 0x00FF),
        (0x0100, 0x017F),
        (0x0180, 0x024F),
        (0x2C60, 0x2C7F),
        (0x16A0, 0x16F0),
        (0x0370, 0x0377),
        (0x037A, 0x037E),
        (0x0384, 0x038A),
        (0x038C, 0x038C),
    ]

    alphabet = [
        get_char(code_point) for current_range in include_ranges
        for code_point in range(current_range[0], current_range[1] + 1)
    ]
    return ''.join(random.choice(alphabet) for i in range(length))
