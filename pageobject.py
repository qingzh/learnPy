#! -*- coding:utf8 -*-


from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import time
from selenium.common.exceptions import NoSuchElementException
from APITest.model.models import _slots_class


def displayed_dec(func):
    def wrapper(*args, **kwargs):
        items = func(*args, **kwargs)
        return filter(lambda x: x.is_displayed() and x.size['height'] * x.size['width'], items)
    return wrapper

WebElement.find_elements = displayed_dec(WebElement.find_elements)

INPUT_TEXT_TYPES = set(('text', 'password'))


PageInfo = _slots_class(
    'PageInfo', ('currentPage', 'level', 'totalPage', 'totalRecord'))


def _find_input(element):
    '''
    find input except `readonly` input
    '''
    if element.tag_name == 'input':
        return element
    _inputs = element.find_elements(By.XPATH, './/input[not(@readonly)]')
    if not _inputs:
        return None
    if len(_inputs) == 1:
        return _inputs[0]
    raise Exception("Too many input!")


def _set_input(element, value):
    if element.get_attribute('type') in INPUT_TEXT_TYPES:
        element.clear()
        element.send_keys(value)
    else:
        if value != element.is_selected():
            element.click()


class BasePage(object):

    def __init__(self, driver, by=None, locator=None):
        self.driver = driver
        self.by = by
        self.locator = locator

    @property
    def root(self):
        '''
        the root of the Page
        maybe a `driver` or a `WebElement`
        '''
        if self.by is not None:
            return self.driver.find_element(self.by, self.locator)
        else:
            return self.driver


class BaseContainer(BasePage):

    _root = None

    def __init__(self, driver=None, by=None, locator=None):
        '''
        Container's driver could be None
        '''
        # Do NOT use self.driver = driver ...
        self._driver = driver
        self.by = by
        self.locator = locator

    @property
    def driver(self):
        return self._driver

    @property
    def root(self):
        '''
        self.driver: logic parent of self.root
        '''
        if self._root is None:
            self._root = super(BaseContainer, self).root
        if not self._root.is_displayed():
            self.driver.click()
        return self._root


class BasePageElement(object):

    '''
    @attr by: By.XPATH, By.CLASS, ...
    @attr locator:
    '''

    def __init__(self, by, locator):
        self.by = by
        self.locator = locator

    def __get__(self, obj, objtype=None):
        '''
        property `root` is dynamic, it's IMPORTANT
        return WebElement
        '''
        return obj.root.find_element(self.by, self.locator)


class ListElement(BasePageElement):

    def __get__(self, obj, objtype=None):
        '''

        return WebElement
        '''
        root = obj.root
        return root.find_elements(self.by, self.locator)


class ClickElement(BasePageElement):

    def __set__(self, obj, value=True):
        '''
        @param value: click if value == True else do nothing
        '''
        if value:
            self.__get__(obj).click()


class CheckboxElement(BasePageElement):

    def __set__(self, obj, value):
        element = self.__get__(obj)
        if value == element.is_selected():
            return
        element.click()


class FormElement(BasePageElement)
    pass


class SelectorElement(BasePageElement):

    def __init__(self, by, locator, subloc):
        super(SelectorElement, self).__init__(by, locator)
        self.subloc = subloc

    def __get__(self, obj, objtype=None):
        element = super(SelectorElement, self).__get__(obj, objtype)
        return element.find_elements(*self.subloc)


class InputElement(BasePageElement):

    def __set__(self, obj, value):
        element = self.__get__(obj)
        element = _find_input(element)
        if element is None:
            raise TypeError("Not `input` element!")
        _set_input(element, value)


class AlertElement(ClickElement):

    def __set__(self, obj, value):
        element = super(AlertElement, self).__get__(obj)
        element.click()
        alert = element.parent.switch_to_alert()
        if value is None:
            return
        if value:
            alert.accept()
        else:
            alert.dismiss()

    def __get__(self, obj, objtype=None):
        '''
        return alert instead of `WebElement`
        '''
        element = super(AlertElement, self).__get__(obj, objtype)
        element.click()
        return element.parent.switch_to_alert()


class ContainerElement(BasePageElement):

    """
    # TODO
    现在ContainerElement是允许装配的
    能不能让 Page也允许装配？

    """
    _container_ = None

    def __init__(self, by, locator, obj, *args, **kwargs):
        '''
        by
        locator
        obj: container hook
        '''
        super(ContainerElement, self).__init__(by, locator)
        if type(obj) is type:
            self._container_hook_ = obj
            self._args_ = args
            self._kwargs_ = kwargs
        else:
            self._container_ = obj

    def __get__(self, obj, objtype=None):
        '''
        return a `Container Object` instead of a `WebElement`
        '''
        root = super(ContainerElement, self).__get__(obj, objtype)
        if self._container_ is None:
            self._container_ = self._container_hook_(
                root, *self._args_, **self._kwargs_)
        self._container_.driver = root
        return self._container_


class BatchUlContainer(BaseContainer):

    suspend = AlertElement(
        By.XPATH, '//li[contains(@class, "stop-promotion")]')
    # resume = ClickElement(By.CSS_SELECTOR, 'li.start-promotion')
    resume = AlertElement(
        By.XPATH, '//li[contains(@class, "start-promotion")]')
    budget = ClickElement(
        By.XPATH, '//li[contains(@class, "modify-budget")]')
    price = ClickElement(By.XPATH, '//li[contains(@class, "modify-price")]')
    # budget = ClickElement(By.CSS_SELECTOR, 'li.modify-budget')
    # price = ClickElement(By.CSS_SELECTOR, 'li.modify-price')
    # match_pattern = ClickElement(By.CSS_SELECTOR, 'li.match_pattern')
    match_pattern = ClickElement(
        By.XPATH, '//li[contains(@class, "match_pattern")]')
    delete = AlertElement(By.CSS_SELECTOR, 'li.delete-item')


class NameEditContainer(BaseContainer):
    text = InputElement(By.XPATH, './/input[@class="edit_text"]')
    confirm = InputElement(By.XPATH, './/input[@class="edit_confirm"]')
    cancel = InputElement(By.XPATH, './/input[@class="edit_cancel"]')

name_editor = NameEditContainer(
    None, By.XPATH, '//div[@class="tableOpenWin"]/div[@class="inputBlank"]')


class ListContainer(BaseContainer, list):

    '''
    attributes: `driver` and `root`
    do Initialization of list when set `driver`
    '''

    def __init__(self, driver=None, by=None, locator=None, subxpath=None, subobj=None):
        '''
        find all leaf nodes with no-blank displayed text
        element with no child: `*[not(child::*)]` or `*[not(*)]`
        `not(*)` means "does not have any element child"
        `*` means "selectes all element children of the context node"
        '''
        super(ListContainer, self).__init__(driver, by, locator)
        self.subxpath = subxpath or './/*[not(*) and text() != ""]'
        self.subobj = subobj

    @driver.setter
    def driver(self, value):
        '''
        TODO: Initialized with `WebElement` ?
        `self.subobj(WebElement)`
        '''
        self._driver = value
        items = self._driver.find_elements(By.XPATH, self.subxpath)
        if self.subobj is not None:
            list.__init__(self, (self.subobj(x) for x in items))
        else:
            list.__init__(self, items)

    def __setitem__(self, key, value):
        '''
        (True, False, None): click
        (basestring): send_keys
        '''
        element = self[key]
        element = _find_input(element) or element
        _set_input(element, value)


class DictContainer(BaseContainer, dict):

    '''
    attributes: `driver` and `root`
    do Initialization of dict when set `driver`
    '''

    def __init__(self, driver=None, by=None, locator=None, subxpath=None):
        '''
        find all leaf nodes with no-blank displayed text
        element with no child: `*[not(child::*)]` or `*[not(*)]`
        `not(*)` means "does not have any element child"
        `*` means "selectes all element children of the context node"
        '''
        super(DictContainer, self).__init__(driver, by, locator)
        self.subxpath = subxpath or './/*[not(*) and text() != ""]'

    @driver.setter
    def driver(self, value):
        self._driver = value
        items = self._driver.find_elements(
            By.XPATH, self.subxpath)
        dict.__init__(self, ((x.text, x) for x in items))

    def __setitem__(self, key, value):
        '''
        (True, False, None): click
        (basestring): send_keys
        '''
        element = self[key]
        '''
        if isinstance(value, basestring):
            element.send_keys(value)
            return
        '''
        # `input` item
        element = _find_input(element) or element
        _set_input(element, value)


class AddPlanContainer(BaseContainer):
    #
    name = InputElement(
        By.XPATH, '//p[@class="formTitle"][1]/following-sibling::*[1]')
    # `radio`
    region = InputElement(
        By.XPATH, '//p[@class="formTitle"][2]/following-sibling::*[1]')
    budget = InputElement(
        By.XPATH, '//p[@class="formTitle"][3]/following-sibling::*[1]')
    opts = ContainerElement(
        By.XPATH, './/div[@class="form-footer form-bottom-big"]',
        DictContainer, subxpath='./a[@class]')


class TRContainer(BasePage):

    checkbox = CheckboxElement(By.XPATH, './/input')


class TableContainer(BasePage):
    header = ContainerElement(By.XPATH, './thead/tr', TRContainer)
    body = ListElement(By.XPATH, './tbody/tr')


class SelectorContainer(BasePage):
    header = ContainerElement(
        By.CLASS_NAME, 'select-title', DictContainer, './/li[text() != ""]')
    content = ContainerElement(
        By.CLASS_NAME, 'select-content', DictContainer, './/li[*/text() != ""]')


class DateContainer(BasePage):

    '''
    Date format: '2015-01-01'
    >>> date = DateContainer(driver, by, locator)
    >>> date.start_date = '2015-01-01'
    >>> date.header.get(u'本月').click()
    '''

    header = ContainerElement(
        By.XPATH, './/div[@class="fast-link"]', DictContainer)
    start_date = InputElement(By.XPATH, './/input[1]')
    end_date = InputElement(By.XPATH, './/input[2]')


class TabContainer(BasePage):

    """
    为什么要两层property?
    TODO: refactor

    或者能否保留 ContainerElement 这层的对象?
    意即：

    """
    add = ContainerElement(
        By.ID, 'addBtn',
        AddPlanContainer(None, By.XPATH, '//div[@class="addPlanWin"]')
    )
    batch = ContainerElement(
        By.ID, 'manyDo',
        BatchUlContainer(None, By.XPATH, '//div[contains(@class, "plcz-ul")]')
    )
    # By.XPATH, '//div[contains(@class, "plcz-ul")]', BatchUlContainer)
    # By.CSS_SELECTOR, 'div.plcz-ul', DictContainer)
    row_button = ClickElement(By.ID, 'definRow')
    _row_title = ContainerElement(
        By.XPATH, '//div[contains(@class, "columnWin")]', SelectorContainer)
    date_button = ClickElement(By.XPATH, './/div[@class="fn-dates-picker"]')
    _date_picker = ContainerElement(
        By.XPATH, './/div[@class="fn-date-container right"]', DateContainer)
    table = ContainerElement(
        By.CSS_SELECTOR, 'table.main-table', TableContainer)
    """
    @property
    def batch(self):
        element = self._batch
        if not element.root.is_displayed():
            self.batch_button = True
        return element
    """
    @property
    def row_title(self):
        element = self._row_title
        if not element.root.is_displayed():
            self.row_button = True
        return element

    @property
    def date_picker(self):
        element = self._date_picker
        if not element.root.is_displayed():
            self.date_button = True
        return element


class DaysContainer(BaseContainer):

    header = ContainerElement(
        By.XPATH,
        './/ul[@class="timeWin-quick-ul"]',
        DictContainer, subxpath='.//li[@class]'
    )
    days = ContainerElement(
        By.XPATH,
        './/div[@class="win-c"]',
        DictContainer, subxpath='.//div[@class="time-data"]'
    )
    opts = ContainerElement(
        By.XPATH,
        './/div[@class="form-footer"]',
        DictContainer, subxpath='.//a[@class]'
    )


class LoginPage(BasePage):

    username = InputElement(By.XPATH, '//input[@id="username"]')
    password = InputElement(By.XPATH, '//input[@id="password"]')
    captcha = InputElement(By.XPATH, '//input[@name="captchaResponse"]')
    submit = ClickElement(By.XPATH, '//input[@name="submit"]')


class AdManagementPage(BasePage):
    pass


class TabPage(BasePage):
    tab = ContainerElement(By.CLASS_NAME, 'main-nav-content', TabContainer)
    numbers = ListElement(By.CSS_SELECTOR, 'li.page-item')
    allRecords = CheckboxElement(By.ID, 'showAllRecords')

url = 'http://42.120.168.74'


def login(driver):
    driver.get(url)
    page = LoginPage(driver)
    page.username = 'ShenmaPM2.5'
    page.password = 'pd123456'
    page.captcha = '1'
    page.submit = True


def _show_all(page):
    page.tab.header.row_title.header[u'全部'] = True


def _batch_resume(page):
    page.tab.batch.resume = None
    alert = page.driver.switch_to_alert()
    expected = u'是否确认恢复所有选中的'
    assert alert.text.startswith(expected), u'Text not matched!\nExpected: "%s"\nActual: "%s"' % (
        expected, alert.text)
    alert.accept()


def batch_resume(driver):
    page = TabPage(driver)
    # Choose Single Page
    page.tab.table.header.checkbox = True
    _batch_resume(page)

    time.sleep(3)
    # Choose Multi Page
    if len(page.numbers) > 1:
        page.tab.table.header.checkbox = True
        page.allRecords = True
        _batch_resume(page)
