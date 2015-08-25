#! -*- coding:utf8 -*-

# 希望这里的WebElement是修改以后的
from .compat import By, WebElement
import random
import string

__all__ = ['_find_input', '_set_input', 'len_unicode', 'kwargs_dec',
           '_find_and_set_input', 'gen_random_ascii', 'gen_chinese_unicode']

INPUT_TEXT_TYPES = set(('text', 'password'))


def kwargs_dec(func, **dec_kwargs):
    def wrapper(*args, **kwargs):
        kwargs.update(dec_kwargs)
        return func(*args, **kwargs)
    return wrapper


def len_unicode(s, encoding='utf8'):
    '''
    unicode lenght in python is 3-bytes
    convert it into 2-bytes

    >>> len(u'哈哈')
    6
    >>> len_unicode(u'哈哈')
    4
    >>> len(u'哈哈a')
    7
    >>> len_unicode(u'哈哈a')
    5
    '''
    if isinstance(s, str):
        return (len(s) + len(s.decode(encoding))) / 2
    return (len(s.encode(encoding)) + len(s)) / 2


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
