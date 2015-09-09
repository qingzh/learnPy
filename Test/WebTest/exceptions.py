#! -*- coding:utf8 -*-


from selenium.common.exceptions import (
    NoSuchElementException, ElementNotVisibleException, WebDriverException)


class NoPerformanceEntry(Exception):
    pass
