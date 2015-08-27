#! -*- coding:utf8 -*-

"""

`InputElement`
把控件的操作抽象出来，无非2种：
1. 单击 (选中，不选中，纯点击)
2. 输入文本

TODO:
 将 list dict 变成 iterator 提高性能？

TODO:
 只有root元素变的时候才需要修改元素
 如何利用这个进行优化？

"""

from ..utils import *
from ..compat import (
    By, WebElement, NoSuchElementException, ElementNotVisibleException)
from APITest.models.models import _slots_class
import logging

log = logging.getLogger(__name__)

__all__ = ['BaseElement', 'InputElement', 'AlertElement', 'ListElement',
           'DictElement', 'BasePage', 'ContainerElement', 'BaseContainer',
           'ListContainer', 'DictContainer', 'PageInfo', 'StatusElement',
           'LoginPage']


PageInfo = _slots_class(
    'PageInfo', ('currentPage', 'level', 'totalPage', 'totalRecord', 'pageIndex'))

##########################################################################
#  Timing Decorator

'''
# 获取 Chrome 提供的 HTML5 Performance Timing 对象
entries = AttributeDict(
    driver.execute_script('return window.performance.getEntries()'))
for entry in entries:
    if entry.name.index(pattern):
        duration = entry.requestStart - entry.responseStart
'''


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
        if isinstance(obj, WebElement):
            try:
                item = obj.find_element(self.by, self.locator)
            except (NoSuchElementException, ElementNotVisibleException):
                obj.click()
                item = obj.find_element(self.by, self.locator)
            return item
        try:
            return obj.root.find_element(self.by, self.locator)
        except Exception as e:
            log.debug(
                'Obj:%s\nSelf:%s\nParent:%s, By:%s, Locator:%s', type(obj), type(self), obj.parent, self.by, self.locator)
            raise e


class InputElement(BaseElement):

    def __set__(self, obj, value):
        # __get__ 的时候碰到异常
        item = super(InputElement, self).__get__(obj)
        element = _find_input(item) or item
        if element is None:
            raise TypeError("Not `input` element!")
        _set_input(element, value)


"""
由于key_map的存在
是否可以复用DictContainer??
    修改 __set__ 方法
"""


class StatusElement(BaseElement):

    '''
    轮选
    '''

    def __init__(self, by, locator, key, key_map):
        '''
        key: the value of the WebElement

        key_map = {
            u'暂停': 'pause',
            u'恢复': 'run'
        }

        key = lambda x: x.get_attribute('class').rpartition(' ')[-1]
        '''
        self.by = by
        self.locator = locator
        self._key = key
        self._map = key_map

    def __get__(self, obj, objtype=None):
        item = super(StatusElement, self).__get__(obj)
        return self._key(item)

    def __set__(self, obj, value):
        if value not in self._map:
            raise Exception('Status is not supported!')
        log.debug('StatusElement: %s\n', self.__dict__)
        status = self._map[value]
        item = super(StatusElement, self).__get__(obj)
        origin = current = self._key(item)
        if status == current:
            return
        while True:
            '''
            有可能状态就是遍历不到
            '''
            item.click()
            item = super(StatusElement, self).__get__(obj)
            current = self._key(item)
            log.debug('StatusElement current status: %s', current)
            if status == current or origin == current:
                return
    """
TODO:
  ListElement, DictElement
  目前 _subxpath 只支持xpath这种形式
  应为 '(%s)[%d]' 只对xpath生效，对css无效
  css为 ' :eq(%d)'

TODO:
.parent, .root 的传递
"""

_selector_dict = {
    By.XPATH: '(%s)[%d]',
    By.CSS_SELECTOR: '%s:eq(%d)',
}


class ListMixin(list):

    def __getitem__(self, key):
        item = super(ListMixin, self).__getitem__(key)
        if hasattr(item, '__get__'):
            return item.__get__(self, type(self))
        else:
            return item

    def __setitem__(self, key, value):
        '''
        We assume that item is an `object`
        需要动态查看是否有 __set__ 方法，然后调用
        否则只需要 _set_input
        '''
        item = super(ListMixin, self).__getitem__(key)
        if hasattr(item, '__set__'):
            item.__set__(self, value)
            return
        item = self.__getitem__(key)
        _find_and_set_input(item)

    def __iter__(self):
        return (self.__getitem__(i) for i in xrange(len(self)))


class DictMixin(dict):

    def __getitem__(self, key):
        item = super(DictMixin, self).__getitem__(key)
        if hasattr(item, '__get__'):
            return item.__get__(self, type(self))
        else:
            return item

    def __setitem__(self, key, value):
        '''
        (True, False, None): click
        (basestring): send_keys
        '''
        item = super(DictMixin, self).__getitem__(key)
        if hasattr(item, '__set__'):
            item.__set__(self, value)
            return
        item = self.__getitem__(key)
        _find_and_set_input(item, value)

    def __iter__(self):
        return (self.__getitem__(i) for i in self.keys())

    def items(self):
        raise AttributeError("It's a property dict, `.items()` forbidden!")

    iteritems = items


class ContainerElement(BaseElement):

    """
    TODO
    1. 现在ContainerElement是允许装配的
       能不能让 Page也允许装配？
    2. Nested ContainerElement?

    需要注意，如果存在 点击-展现 的行为的话
    ContainerElement 的 parent 节点一定要是 click 的！

    挑战：
    点了 单页 全选，跳出 多页全选
    多页全选不是隐藏的，是js插入的，所以不能通过判断
    .is_displayed()判断，而是通过抓住异常 NoSuchElementException
    """
    _container_ = None

    def __init__(self, by, locator, obj, *args, **kwargs):
        '''
        by
        locator
        obj: container hook
        `args, kwargs` works only if `type(obj) is type`
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
        '''
        如果是 BasePage 则：
        动态设置 .parent, 返回

        如果是 BaseElement, 则递归：
        获取 obj.root，返回值
        '''
        if hasattr(self._container_, '__get__'):
            return self._container_.__get__(root)
        self._container_.parent = root
        return self._container_

    def __set__(self, obj, value):
        '''
        i如果是 property, 则递归：
        调用 __set__

        注意，如果是 ContainerElement(DictContainer)
        这里 __set__ 函数需要修订
        '''
        if hasattr(self._container_, '__set__'):
            root = super(ContainerElement, self).__get__(obj)
            self._container_.__set__(root, value)
        # 其它类型的container
        item = self.__get__(obj)
        if hasattr(item, '__contains__') and value in item:
            '''
            item[value] 调用了 DictContainer 的 __setitem__
            '''
            item[value] = True
        # Do nothing


class ListElement(ContainerElement):

    def __init__(self, by, locator, subobj=None):
        '''
        @param subobj: BaseElement or BaseContainer
        '''
        subobj = subobj or BaseElement
        super(ListElement, self).__init__(
            By.XPATH, '.', ListContainer,
            subby=by, subxpath=locator, subobj=subobj)

    '''
    def __get__(self, obj, objtype=None):
        root = obj.root
        if issubclass(self._subobj, BaseElement):
            self._init = lambda x, y: self._subobj(x, y)
        else:
            self._init = lambda x, y: self._subobj(root, x, y)
        items = root.find_elements_with_index(self.by, self.locator)
        return ListMixin(
            (self._init(self.by, '(%s)[%d]' %
                        (self.locator, i + 1)) for i, x in items)
        )
    '''


class DictElement(ContainerElement):

    """
    Like DictContainer
    by: By.XPATH
    locator: subxpath
    """

    def __init__(self, by, locator, subobj=None, key=None):
        '''
        @param subobj: BaseElement or BaseContainer
        '''
        key = key or (lambda x: x.text.strip())
        subobj = subobj or BaseElement
        super(DictElement, self).__init__(
            By.XPATH, '.', DictContainer,
            subby=by, subxpath=locator, subobj=subobj, key=key)

    """
    __get__ 返回的是一个字典
    __getitem__ 应该修改的是返回的字典><

    重构一个Dict类

    应该是一次性生成所有元素，再动态设置root
    DictElement的subobj也是Property

    # Nested property
    """
'''
    def __get__(self, obj, objtype=None):
        root = obj.root
        if issubclass(self._subobj, BaseElement):
            self._init = lambda x, y: self._subobj(x, y)
        else:
            self._init = lambda x, y: self._subobj(root, x, y)
        items = root.find_elements_with_index(self.by, self.locator)
        return DictMixin(
            (self._key(x), self._init(
                self.by, '(%s)[%d]' % (self.locator, i + 1)))
            for i, x in items
        )
'''


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
        element = super(AlertElement, self).__get__(obj)
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

    def _click_parent(self):
        try:
            self.parent.click()
        except ElementNotVisibleException:
            # mouse over `self.parent` element
            self.parent.find_element(By.XPATH, '..').click()
            self.parent.click()

    @property
    def root(self):
        '''
        动态取得 root 节点
        self.parent: logic parent of self.root
        '''
        try:
            self._root = super(BaseContainer, self).root
        except NoSuchElementException:
            log.debug(
                'Root is not found. Type: %s\ndict: %s\n', type(self), self.__dict__)
            self._click_parent()
            self._root = super(BaseContainer, self).root
        try:
            if not self._root.is_displayed():
                self._click_parent()
        except Exception as e:
            log.debug(
                'Type: %s, root:%s\n%s\n', type(self), self._root, self.__dict__)
            # log.debug(e)
            raise e
        return self._root


class ListContainer(BaseContainer, ListMixin):

    '''
    attributes: `parent` and `root`
    do Initialization of list when set `parent`

    还需要实现 __contains__
          以及 __iter__: 用于循环遍历
    '''

    def __init__(self, parent=None, by=None, locator=None, subby=None, subxpath=None, subobj=None, visible=True):
        '''
        find all leaf nodes with no-blank displayed text
        element with no child: `*[not(child::*)]` or `*[not(*)]`
        `not(*)` means "does not have any element child"
        `*` means "selectes all element children of the context node"

        @param subobj: BaseElement or BaseContainer
        '''
        super(ListContainer, self).__init__(parent, by, locator)
        self._subby = subby or By.XPATH
        self._subxpath = subxpath or './/*[not(*) and text() != ""]'
        self._subobj = subobj or BaseElement
        self._visible = visible

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
        root = self.root
        if issubclass(self._subobj, BaseElement):
            init = lambda x, y: self._subobj(x, y)
        else:
            init = lambda x, y: self._subobj(root, x, y)
        items = root.find_elements_with_index(
            self._subby, self._subxpath, self._visible)
        # 这里也需要动态配置
        # 否则刷新页面页面之后，就会报错
        # 比如，测试页头的几个链接，页头的元素xpath不会变化
        # 但是点击页头之后刷新的页面，页头元素的python object已经改变

        # `BaseElement`
        # 这里有个问题，items拿到的是显示出来的item
        # 怎么让subxpath去匹配显示的item
        list.__init__(
            self,
            (init(
                self._subby, _selector_dict[self._subby] % (self._subxpath, i + 1)) for i, x in items)
        )
        # TODO: `BaseContainer` ??

'''

怎么实现 .items, .iteritems() 并实现赋值
对于 items() 操作，实际上取出来的是property
但是已经无法获得关联的obj，所以...？
再给 BaseElement 动态分配一个root？ 不可能。

禁掉这俩功能>< items...

'''


class DictContainer(BaseContainer, DictMixin):

    '''
    attributes: `parent` and `root`
    do Initialization of dict when set `parent`
    '''

    def __init__(self, parent=None, by=None, locator=None, subby=None, subxpath=None, subobj=None, key=None, visible=True):
        '''
        find all leaf nodes with no-blank displayed text
        element with no child: `*[not(child::*)]` or `*[not(*)]`
        `not(*)` means "does not have any element child"
        `*` means "selectes all element children of the context node"
        subobj 必须是 class? 如果是 instance 呢？

        TODO:
            subobj 是一个 class property
        '''
        super(DictContainer, self).__init__(parent, by, locator)
        self._subby = subby or By.XPATH
        self._subxpath = subxpath or './/*[not(*) and text() != ""]'
        self._subobj = subobj or BaseElement
        self._key = key or (lambda x: x.text.strip())
        self._visible = visible

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value
        root = self.root
        '''
        TODO:
        这里最好是改成 self._subobj(by=x, locator=y)
        然后再手动设置 .parent = root
        即使是 BaseElement 也能设置 .parent
        '''
        if not isinstance(self._subobj, type):
            init = lambda x, y: self._subobj(x, y)
        elif issubclass(self._subobj, BaseElement):
            init = lambda x, y: self._subobj(x, y)
        else:
            init = lambda x, y: self._subobj(root, x, y)
        items = root.find_elements_with_index(
            self._subby, self._subxpath, self._visible)
        # print self._subby, self._subxpath, root.text
        # print items
        '''
        初始化
        key: self._key(x), x is the `WebElement` object of node
        value: WebElement
        '''
        '''
        在这里用的是初始化，相当于 update 操作
        应该是 先删除，后覆盖；否则会有 遗留的状态
        '''
        self.clear()
        dict.__init__(self, (
            (self._key(x), init(
                self._subby, _selector_dict[self._subby] % (self._subxpath, i + 1)))
            for i, x in items
        ))


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


##########################################################################
#   其他


class LoginPage(BasePage):

    username = InputElement(By.XPATH, '//input[@id="username"]')
    password = InputElement(By.XPATH, '//input[@id="password"]')
    captcha = InputElement(By.XPATH, '//input[@name="captchaResponse"]')
    submit = InputElement(By.XPATH, '//input[@name="submit"]')
