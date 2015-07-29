#! -*- coding:utf8 -*-


from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

__all__ = ['_find_input', '_set_input', '_find_and_set_input',
           'displayed_dec', 'index_displayed']

INPUT_TEXT_TYPES = set(('text', 'password'))


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


def _find_input(element):
    '''
    find input except `readonly` input
    @param element: Should be instance of WebElement
    '''
    if not isinstance(element, WebElement):
        raise TypeError('Expected WebElement!')
    if element.tag_name == 'input':
        return element
    _inputs = element.find_elements(By.XPATH, './/input[not(@readonly)]')
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
