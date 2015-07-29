#! -*- coding:utf8 -*-

"""

`InputElement`
把控件的操作抽象出来，无非2种：
1. 单击 (选中，不选中，纯点击)
2. 输入文本

"""

from ..utils import _find_input, _set_input
from selenium.webdriver.remote.webelement import WebElement

######################################################################
#  decorate `WebElement.find_elements`
'''
怎么统一让所有文件都 import 同一个module
借鉴： requests的做法？
'''
if not hasattr(WebElement, '_find_elements'):
    WebElement._find_elements = WebElement.find_elements

WebElement.find_elements_with_index = index_displayed(
    WebElement._find_elements)

WebElement.find_elements = displayed_dec(WebElement._find_elements)

######################################################################

__all__ = ['BaseElement', 'InputElement']


##########################################################################
#  element 类


class BaseElement(object):

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


class InputElement(BaseElement):

    def __set__(self, obj, value):
        item = self.__get__(obj)
        element = _find_input(item) or item
        if element is None:
            raise TypeError("Not `input` element!")
        _set_input(element, value)


class ListElement(BaseElement):

    def __get__(self, obj, value):
        items = obj.root.find_elements_with_index(self.by, self.locator)
        return [self._init(self.by, self.locator + '[%d]' % (i + 1)) for i, x in items]

    def __init__(self, by, locator, subobj=None):
        '''
        @param subobj: BaseElement or BaseContainer
        '''
        super(ListElement, self).__init__(by, locator)
        subobj = subobj or BaseElement
        if issubclass(subobj, BaseElement):
            self._init = lambda x, y: subobj(x, y)
        else:
            # 怎么让self.root也变成动态的?
            self._init = lambda x, y: subobj(self.root, x, y)


class ContainerElement(BaseElement):

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
                None, *self._args_, **self._kwargs_)
        self._container_.parent = root
        return self._container_


class AlertElement(InputElement):

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

##########################################################################
# Container/Page 类


class BasePage(object):

    def __init__(self, parent, by=None, locator=None):
        self.parent = parent
        self.by = by
        self.locator = locator

    @property
    def root(self):
        '''
        the root of the Page
        maybe a `parent` or a `WebElement`
        '''
        if self.by is not None:
            return self.parent.find_element(self.by, self.locator)
        else:
            return self.parent


class BaseContainer(BasePage):

    _root = None

    def __init__(self, parent=None, by=None, locator=None):
        '''
        Container's parent could be None
        self._parent: parent of `self.root`
        self.root: `root` node located by `self.by` and `self.locator`
        '''
        # Do NOT use self.parent = parent ...
        self._parent = parent
        self.by = by
        self.locator = locator

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def root(self):
        '''
        动态取得 root 节点
        self.parent: logic parent of self.root
        '''
        self._root = super(BaseContainer, self).root
        if not self._root.is_displayed():
            try:
                self.parent.click()
            except ElementNotVisibleException:
                # mouse over `self.parent` element
                self.parent.find_element(By.XPATH, '..').click()
                self.parent.click()
        return self._root


class ListContainer(BaseContainer, list):

    '''
    attributes: `parent` and `root`
    do Initialization of list when set `parent`

    还需要实现 __contains__
          以及 __iter__: 用于循环遍历
    '''

    def __init__(self, parent=None, by=None, locator=None, subxpath=None, subobj=None):
        '''
        find all leaf nodes with no-blank displayed text
        element with no child: `*[not(child::*)]` or `*[not(*)]`
        `not(*)` means "does not have any element child"
        `*` means "selectes all element children of the context node"

        @param subobj: BaseElement or BaseContainer
        '''
        super(ListContainer, self).__init__(parent, by, locator)
        self.subxpath = subxpath or './/*[not(*) and text() != ""]'
        subobj = subobj or BaseElement
        if issubclass(subobj, BaseElement):
            self._init = lambda x, y: subobj(x, y)
        else:
            # 怎么让self.root也变成动态的?
            self._init = lambda x, y: subobj(self.root, x, y)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        '''
        TODO: Initialized with `WebElement` ?
        `self.subobj(WebElement)`
        '''
        self._parent = value
        items = self.root.find_elements_with_index(By.XPATH, self.subxpath)
        # 这里也需要动态配置
        # 否则刷新页面页面之后，就会报错
        # 比如，测试页头的几个链接，页头的元素xpath不会变化
        # 但是点击页头之后刷新的页面，页头元素的python object已经改变

        # `BaseElement`
        # 这里有个问题，items拿到的是显示出来的item
        # 怎么让subxpath去匹配显示的item
        list.__init__(
            self,
            (self._init(
                By.XPATH, self.subxpath + '[%d]' % (i + 1)) for i, x in items)
        )
        # TODO: `BaseContainer` ??

    def __getitem__(self, key):
        item = super(ListContainer, self).__getitem__(key)
        if hasattr(item, '__get__'):
            return item.__get__(self, type(self))
        else:
            return item

    def __setitem__(self, key, value):
        '''
        We assume that item is an `object`
        '''
        item = self.__getitem__(key)
        element = _find_input(item) or item
        _set_input(element, value)

    def __iter__(self):
        return (self.__getitem__(i) for i in xrange(len(self)))


class DictContainer(BaseContainer, dict):

    '''
    attributes: `parent` and `root`
    do Initialization of dict when set `parent`
    '''

    def __init__(self, parent=None, by=None, locator=None, subxpath=None, subobj=None, key=None):
        '''
        find all leaf nodes with no-blank displayed text
        element with no child: `*[not(child::*)]` or `*[not(*)]`
        `not(*)` means "does not have any element child"
        `*` means "selectes all element children of the context node"
        '''
        super(DictContainer, self).__init__(parent, by, locator)
        self.subxpath = subxpath or './/*[not(*) and text() != ""]'
        subobj = subobj or BaseElement
        if issubclass(subobj, BaseElement):
            self._init = lambda x, y: subobj(x, y)
        else:
            # 怎么让self.root也变成动态的?
            self._init = lambda x, y: subobj(self.root, x, y)
        self._key = key or (lambda x: x.text)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value
        items = self.root.find_elements_with_index(By.XPATH, self.subxpath)
        '''
        初始化
        key: self._key(x), x is the `WebElement` object of node
        value: WebElement
        '''
        dict.__init__(self, (
            (self._key(x), self._init(
                By.XPATH, self.subxpath + '[%d]' % (i + 1)))
            for i, x in items
        ))

    def __getitem__(self, key):
        item = super(DictContainer, self).__getitem__(key)
        if hasattr(item, '__get__'):
            return item.__get__(self, type(self))
        else:
            return item

    def __setitem__(self, key, value):
        '''
        (True, False, None): click
        (basestring): send_keys
        '''
        item = self.__getitem__(key)
        element = _find_input(item) or item
        _set_input(element, value)

    def __iter__(self):
        return (self.__getitem__(i) for i in self.keys())

##########################################################################
#   其他


class MouseOverMixin(BasePage):

    @property
    def root(self):
        '''
        self.parent: logic parent of self.root
        '''
        if self._root is None:
            self._root = super(BaseContainer, self).root
        if not self._root.is_displayed():
            try:
                self.parent.click()
            except ElementNotVisibleException:
                # mouse over `self.parent` element
                self.parent.find_element(By.XPATH, '..').click()
                self.parent.click()
        return self._root
