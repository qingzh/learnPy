#! -*- coding:utf8 -*-


from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import time


def displayed_dec(func):
    def wrapper(*args, **kwargs):
        items = func(*args, **kwargs)
        return filter(lambda x: x.is_displayed() and x.size['height'] * x.size['width'], items)
    return wrapper

WebElement.find_elements = displayed_dec(WebElement.find_elements)


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
        print 'ROOT', self, self.by, self.locator
        if self.by is not None:
            return self.driver.find_element(self.by, self.locator)
        else:
            return self.driver


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


class FormElement(BasePageElement):
    pass


class SelectorElement(BasePageElement):

    def __init__(self, by, locator, subloc):
        super(SelectorElement, self).__init__(by, locator)
        self.subloc = subloc

    def __get__(self, obj, objtype=None):
        element = super(SelectorElement, self).__get__(obj, objtype)
        return element.find_elements(*self.subloc)


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
    _container_ = None

    def __init__(self, by, locator, obj):
        '''
        by
        locator
        obj: container hook
        '''
        super(ContainerElement, self).__init__(by, locator)
        if type(obj) is type:
            self._container_hook_ = obj
        else:
            self._container_ = obj

    def __get__(self, obj, objtype=None):
        '''
        return a `Container Object` instead of a `WebElement`
        '''
        if self._container_ is None:
            """
            这里用 by, locator 取定义container
            还是用 WebElement(by, locator) 取定义container?
            """
            self._container_ = self._container_hook_(
                obj.root, self.by, self.locator)
        return self._container_


class BatchUlContainer(BasePage):

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


class ULContainer(BasePage):

    def __init__(self, *args, **kwargs):
        super(ULContainer, self).__init__(*args, **kwargs)
        items = self.root.find_elements(By.XPATH, './/*[text() != ""]')
        for item in items:
            self.__dict__[item.text] = item

    def __getitem__(self, key, value=None):
        if key not in self.__dict__:
            return value
        return self.__dict__[key]


class TRContainer(BasePage):

    checkbox = CheckboxElement(By.XPATH, './/input')


class TableContainer(BasePage):
    header = ContainerElement(By.XPATH, './thead/tr', TRContainer)
    body = ListElement(By.XPATH, './tbody/tr')


class SelectorContainer(BasePage):
    header = ContainerElement(By.CLASS_NAME, 'select-title', ULContainer)


class DateContainer(BasePage):

    header = ContainerElement(
        By.XPATH, './/div[@class="fast-link"]', ULContainer)


class TabContainer(BasePage):

    add_button = FormElement(By.ID, 'addBtn')
    batch_button = ClickElement(By.ID, 'manyDo')
    _batch = ContainerElement(
        By.XPATH, '//div[contains(@class, "plcz-ul")]', BatchUlContainer)
    # By.CSS_SELECTOR, 'div.plcz-ul', ULContainer)
    row_button = ClickElement(By.ID, 'definRow')
    _row_title = ContainerElement(
        By.XPATH, '//div[contains(@class, "columnWin")]', SelectorContainer)
    date_button = ClickElement(By.XPATH, './/div[@class="fn-dates-picker"]')
    _date_picker = ContainerElement(
        By.XPATH, './/div[@class="fn-date-container right"]', DateContainer)
    table = ContainerElement(
        By.CSS_SELECTOR, 'table.main-table', TableContainer)

    @property
    def batch(self):
        element = self._batch
        if not element.root.is_displayed():
            self.batch_button = True
        return element

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


class InputElement(BasePageElement):

    def __set__(self, obj, value):
        element = self.__get__(obj)
        element.clear()
        element.send_keys(value)


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
    page.submit


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
