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
    CustomProperty, By, WebElement,
    WebDriver, NoSuchElementException, ElementNotVisibleException)
from APITest.models.models import _slots_class
import logging

log = logging.getLogger(__name__)

__all__ = ['BaseElement', 'InputElement', 'AlertElement', 'ListElement',
           'DictElement', 'BaseContainer', 'ContainerElement', 'BaseContainer',
           'ListContainer', 'DictContainer', 'PageInfo', 'StatusElement',
           'LoginPage', 'BaseTableContainer']


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


class BaseElement(property):

    '''
    @attr by: By.XPATH, By.CLASS, ...
    @attr locator:
    根据附属的 BaseContainer 对象决定元素位置
    BaseContainer.root.find_element(by, locator)
    '''
    """ FIXME
    感觉…… BaseElement 可以做成 (parent=None) 的 BaseContainer
    """

    def __init__(self, by, locator):
        self.by = by
        self.locator = locator

    def __get__(self, obj, objtype=None):
        '''
        property `root` is dynamic, it's IMPORTANT
        return WebElement
        '''
        if obj is None:
            return self
        #  WebElement
        if not isinstance(obj, WebElement):
            root = obj.root
        else:
            root = obj

        try:
            item = root.find_element(self.by, self.locator)
        except Exception as e:
            log.debug(
                'Obj:%s\nSelf:%s\nParent:%s, By:%s, Locator:%s',
                type(obj), type(self), obj.parent, self.by, self.locator)
            raise e
        '''
        except (NoSuchElementException, ElementNotVisibleException):
            root.click()
            item = root.find_element(self.by, self.locator)
        '''
        return item


class InputElement(BaseElement):

    def __set__(self, obj, value):
        # __get__ 的时候碰到异常
        item = super(InputElement, self).__get__(obj)
        if not isinstance(value, (basestring, bool)):
            value = str(value)
        if item is None:
            raise TypeError("Not `input` element!")
        element = _find_input(item) or item
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
        self.key_map = key_map

    @property
    def key_map(self):
        return self._map

    @key_map.setter
    def key_map(self, value):
        self._map = value

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self._map
        item = super(StatusElement, self).__get__(obj)
        return self._key(item)

    def __set__(self, obj, value):
        if value not in self._map:
            raise Exception('Status is not supported!')
        log.debug('StatusElement: %s\n', self.__dict__)
        status = self._map[value]
        fget = super(StatusElement, self).__get__
        item = fget(obj)
        origin = current = self._key(item)
        if status == current:
            return
        while True:
            '''
            有可能状态就是遍历不到
            '''
            item.click()
            item = fget(obj)
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
        if isinstance(item, property):
            return item.__get__(self, type(self))
        else:
            return item

    def __setitem__(self, key, value):
        '''
        (True, False, None): click
        (basestring): send_keys
        '''
        item = super(DictMixin, self).__getitem__(key)
        if isinstance(item, property):
            item.__set__(self, value)
            # or ?? item = value
            return
        # item = self.__getitem__(key)
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
        if isinstance(obj, type):
            self._container_ = obj(None, *args, **kwargs)

    def __get__(self, obj, objtype=None):
        '''
        return a `Container Object` instead of a `WebElement`
        '''
        if obj is None:
            return self
        root = super(ContainerElement, self).__get__(obj)
        # FIXME
        # Container 也可以设成动态的吧……!!
        # 确实可以，快修修修
        # self._container_ = root
        self._container_.parent = root
        return self._container_

    def __set__(self, obj, value):
        '''
        i如果是 property, 则递归：
        调用 __set__

        注意，如果是 ContainerElement(DictContainer)
        这里 __set__ 函数需要修订
        '''
        if isinstance(value, type):
            raise AttributeError("Can't set to a class type <%s>", value)
        if isinstance(value, BaseContainer):
            self._container_ = value
            return
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

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        # root: WebElement
        root = super(ListElement, self).__get__(obj)
        items = root.find_elements_with_index(
            self.subby, self.subxpath, self.visible)
        if issubclass(self._subobj, BaseElement):
            self._init = lambda x, y: self._subobj(x, y)
        else:
            self._init = lambda x, y: self._subobj(root, x, y)
        items = root.find_elements_with_index(self.by, self.locator)
        return ListMixin(
            (self._init(self.by, '(%s)[%d]' %
                        (self.locator, i)) for i, x in items)
        )


class DictElement(ContainerElement):

    """
    Like DictContainer
    by: By.XPATH
    locator: subxpath
    """

    def __init__(self, by, locator, subobj=None, key=None):
        '''
        字典的 根节点由 by, locator 决定
        子节点由 subby, subxpath, subobj 决定
        { key: (subby, subxpath) }
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

    def __get__(self, obj, objtype=None):
        '''
        __get__ 方法不需要考虑元素是否可见，但是如果本身是 list/dict, 则要考虑生成的列表是否要求可见了
        __set__ 的时候一定要是可见的，所以，需要进行检查~
        '''
        if obj is None:
            return self
        # root: WebElement
        root = self.root = super(ListElement, self).__get__(obj)
        #
        init = lambda x, y: self._subobj(by=x, locator=y)
        items = root.find_elements_with_index(
            self._subby, self._subxpath, self._visible)
        # clear dict
        self.clear()
        # key : (by, locator); 需要动态配置 parent/root 结点
        # 这里的值是property, 存在 __get__, __set__ 方法
        dict.__init__(self, (
            (self._key(x), init(
                self._subby, _selector_dict[self._subby] % (self._subxpath, i)))
            for i, x in items
        ))
        return self

    def get(self, key, default=None):
        return self.__getitem__(key, default)


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


class ParentProperty(property):

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        return obj._parent

    def __set__(self, obj, value):
        if value == obj._parent:
            return value
        obj._change_flag = True
        obj.pset(value)


class RootProperty(property):

    def __get__(self, obj, objtype):
        # 修改 _change_log  部分也提取出来了
        if obj is None:
            return self
        if obj._change_flag:
            # 这样避免使用 obj.parent
            # 因为 obj.parent 的定义就在 ⬆️ \(^o^)/~
            obj.rget(obj._parent)
            obj._change_flag = False
        return obj._root

from functools import update_wrapper


def get_dec(func):
    def wrapper(self, obj, objtype=None):
        if obj is None:
            return self.__class__
        self.parent = obj.root
        if not self._change_flag:
            # 说明没有变化，意即self.root没有变化
            # 注意是 self.root 不是 obj.root
            '''
            这里一定要用 self._element， 因为 
            if not self._change_flag: return self
            而 self._element 实际上就是  child->child->child.__get__(self)

            '''
            return self._element
        return func(self, obj, objtype)
    return update_wrapper(wrapper, func)


class BaseContainer(property):

    '''
    __slots__ 用来记住可以复制的 属性，以及 赋值顺序
    但是，单击呢…… 单击呢
    '''

    def __init__(self, by=None, locator=None, child=None, parent=None):
        ''' 有没有可能 parent 永远不变？
        只有一种可能，parent 是 driver....
        其它没有可能，因为即使xpath是完全一样的，可是元素对象也会不一样
        比如动态刷新了页面，位置完全没变，但是元素对象地址也变了
        '''
        # BaseContainer 不允许设置 parent
        # BasePage 可以
        self._parent = parent
        self.by = by
        self.locator = locator
        self._next = child
        '''
        self._change_flag 记录是否改变了parent，这决定了是否要重新获取root
        True: parent 元素改变了，这表示其他元素也要跟着改变
        Flase: 一旦重新获取了 root 就重新置为 Flase，表示不需要重新获取了
        '''
        self._change_flag = False

    parent = ParentProperty()

    @get_dec
    def __get__(self, obj, objtype=None):
        '''
        这里实际上是 nested property
        obj 和 self 都是 BaseContainer 类型，进行嵌套定义
        return: WebElement or BaseContainer
        这两种返回类型，实际上是有区别的，派生出两种类：
        1. 一定会返回 root
        2. 返回对象本身，但是对象本身的 parent 被动态赋值了

        self._element 记录 chained BaseContainer 的最终结果

        一共有三种返回值：不能返回 root 只能返回 BaseContaner
        self.__class__
        self  （这样 parent, root 都是已经配好的)
        self._element (这是 chained BaseContainer)，用于点击->展现->修改
            self._element 实际上也是一个 BaseContainer 类

        self -> next -> next ... -> BaseContainer(next=None)
                                                                     ↑
        self._element --------------------

        对于 ListContainer, self._root, self._element 都是 list
        '''
        # self.parent = obj.root 就是进行了动态赋值~！ Perfect
        # 继续使用self._change_flag
        child = self._next
        if child is None:
            self._element = self
        else:
            self._element = self._next.__get__(self, type(self))
        return self._element

    def _click_parent(self, level=3):
        parent = self.parent
        elements = []
        for i in range(level):
            try:
                parent.click()
                break
            except ElementNotVisibleException:
                elements.append(parent)
                # mouse over `self.parent` element
                parent = parent.find_element(By.XPATH, '..')
        while elements:
            ele = elements.pop()
            if not ele.is_displayed():
                ele.click()

    def __set__(self, obj, value):
        '''
        这里要检查 可见性！
        这里要不要动态配置 parent ??
        对于 nested property, __set__ 只会到达最后一个？
        比如： a.b.c = '123'
        对于 a,b 是 __get__ 对于 c 才是 __set__(self,b)
        但是点击事件是 chain 起来放在 c 里的…… 所以不用担心 ><~
        '''
        # BaseContainer.__get__ or self.__get__ or super().get
        # 动态设置 root 元素
        # 不使用 self.parent = obj.root
        # 可能会使L原本是 obj.container
        #  但是 通过 obj2.container  也会是 obj.parent  设置的 container
        # 这是不可能的，不可能从其他类调用这个类的成员属性
        # selfparent = obj.root
        """
        这个只能这样赋值： 
        obj.BaseContainer = value
        """
        root, child = self.root, self._next
        if not root.is_displayed():
            ignore_exception(self._click_parent)()
        if child is None:
            return _find_and_set_input(root, value)
        # 这里需要用 child.__set__ 是为了让元素可见
        # 用 self._element 可能元素不可见
        """
        self._element 是在 __get__ 里赋值的
        所以可能取不到！
        """
        # if self._element.root.is_displayed():
        #     return _find_and_set_input(self._element.root, value)
        # 如果还是不可见，就继续点！
        child.__set__(self, value)

    def pset(self, value):
        # _chagne_log 在 Property 类里就改变了，这样就不用每个
        #  继承函数都设置  _change_flag
        self._parent = value

    root = RootProperty()

    def rget(self, parent):
        '''
        Readonly & Dynamic: parent.find_element(by, locator)
        maybe a `parent` or a `WebElement`
        '''
        '''
        动态取得 root 节点
        self.parent: logic parent of self.root

        self._change_flag == false:
        只能说明元素对象没有变，但是元素状态可能是变化的。
        '''
        if self.by is not None:
            self._root = parent.find_element(self.by, self.locator)
        else:
            self._root = parent
        return self._root

    @property
    def text(self):
        '''
        根节点获得的 text 信息
        用来粗糙对比两个页面的文本一致，但是无法比较css样式等
        '''
        root = self.root
        if isinstance(root, WebDriver):
            return root.find_element_by_xpath('//html').text
        # isinstance(root, WebElement):
        return root.text

    @property
    def page_source(self):
        root = self.root
        root = root if isinstance(root, WebDriver) else root.parent
        return root.execute_script('return arguments[0].innerHTML', root)

    def __call__(self, **kwargs):
        '''
        怎么记住 kwargs 的顺序呢
        '''
        for key in kwargs.get('_ordered_key',
                              getattr(self, '_ordered_key', [])):
            if key in kwargs:
                setattr(self, key, kwargs.pop(key))
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def is_displayed(self):
        return self.root.is_displayed()

    def is_enabled(self):
        return self.root.is_enabled()


class BasePage(BaseContainer):

    def __init__(self, parent, by=None, locator=None, child=None):
        super(BasePage).__init__(
            by=by, locator=locator, child=child, parent=parent)

    def __set__(self, obj, value):
        raise Exception("can't set BasePage.parent!")


class FakeObject(object):
    root = None

    def __call__(self, value):
        self.root = value
        return self


class ListContainer(BaseContainer):

    '''
    attributes: `parent` and `root`
    do Initialization of list when set `parent`

    还需要实现 __contains__
          以及 __iter__: 用于循环遍历
    '''

    def __init__(self, locator=None, child=None,  visible=True):
        '''
        find all leaf nodes with no-blank displayed text
        element with no child: `*[not(child::*)]` or `*[not(*)]`
        `not(*)` means "does not have any element child"
        `*` means "selectes all element children of the context node"

        @param subobj: BaseElement or BaseContainer
        '''
        """
        ListContainer: 把 locator 扩展成 [locators]
        DictContainer: 把 locator 扩展成 {key : locators}
        其它的参数都是一样的，多了一个visible 选项~
        by 默认都是 By.XPATH

        parent 还是 parent(父节点的root)
        1. __get__ 需要变化，返回一个list, child需要遍历list成员
        2. 但是root变了，因为locator变成了list，所以需要修改 rget 函数
        """
        super(ListContainer, self).__init__(
            by=By.XPATH, locator=locator, child=child)
        self.locator = locator or './/*[not(*) and text() != ""]'
        self._visible = visible

    @get_dec
    def __get__(self, obj, objtype=None):
        '''
        直接通过 obj.ListContainer  查询
        parent 还是 parent(父节点的root)
        1. __get__ 需要变化，返回一个list, child需要遍历list成员

        如果使用 
        lst = obj.ListContainer
        得到的列表里的元素就是固定的了

        FIXME:
        请根据 __getitem__ 重写
        '''
        # 此时通过self.root 就能获取列表
        # self.root 需要返回一个 list
        fake_obj = FakeObject()
        root, child, t = self.root, self._next, type(self)
        # 这里也需要动态配置
        # 否则刷新页面页面之后，就会报错
        # 比如，测试页头的几个链接，页头的元素xpath不会变化
        # 但是点击页头之后刷新的页面，页头元素的python object已经改变

        # `BaseElement`
        # 这里有个问题，items拿到的是显示出来的item
        # 怎么让subxpath去匹配显示的item
        if child is None:
            # 这里应该是  BaseContainer 数组
            # 数组的 by=By.XPATH, locator=XPATH[i]
            # 或者，只设置parent，不设置 by, locator
            self._element = list(BaseContainer(parent=x) for x in root)
        else:
            self._element = list(child.__get__(fake_obj(x), t) for x in root)
        #!! ListContainer 应该返回一串 property (BaseContainer)

        # 没有child的话就是   self._root 有的话 就是   self._element ?
        #  即使返回的是 Container 列表也没关系
        #  因为 Container 已经设置成了 不通过 实例调用就不能赋值了。
        """
        ListContainer[i]   <--- BaseContainer

        这里返回 self, 则 self._element[i] 的赋值就可以通过
        obj.ListContainer[i] 调用 ListContainer.__setitem__ 来调用
        """
        return self

    def __set__(self, obj, value):
        '''
        禁止通过 obj.ListContainer = value 赋值
        '''
        raise Exception("Can't set value to a list object!")

    def __getitem__(self, idx):
        '''
        通过 (obj.ListContainer)[idx]  查询
        如果 obj 没有变的话，其实elements是不会变的

        __getitem__ 没法获取 obj...

        不要把 root 配成list, 而根据 idx 设置root
        就不需要做任何改变~！

        这里应该和 BaseContainer 一致，返回 BaseContainer 实例
        而不是返回root 

       Q: 那么到底是把 _root 做成 list 还是根据 idx 再取root???

        A: 做成 根据 idx 取 root，则可以返回 
        child.__get__(self)
        '''
        """
        这个适合： l = obj.ListContainer  《-----  ListContainer
                        l[i] = value
        而 el = obj.ListContainer[i]  <<----- BaseContainer
            el = value  <<------ 无效！这样赋值是无效的
            只能 el.__set__()
        是不对的！
        """
        child, obj, t = self_next, self._element[idx], type(self)
        if child is None:
            return obj.__get__(self, t)
        return child.__get__(self, t)

    def __setitem__(self, idx, value):
        '''
        通过 obj.ListContainer[idx] = value 赋值
        '''
        child, obj = self_next, self._element[idx]
        if child is None:
            obj.__set__(self, value)
        else:
            child.__set__(self, value)

    def rget(self, parent):
        '''
        Readonly & Dynamic: parent.find_element(by, locator)
        maybe a `parent` or a `WebElement`
        '''
        self._root = parent.find_elements(
            self.by, self.locator, self.visible)
        return self._root

    @property
    def selected(self):
        for element in self:
            if elemet.is_selected():
                yield element
'''

怎么实现 .items, .iteritems() 并实现赋值
对于 items() 操作，实际上取出来的是property
但是已经无法获得关联的obj，所以...？
再给 BaseElement 动态分配一个root？ 不可能。

禁掉这俩功能>< items...

'''


class DictContainer(BaseContainer):

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

    def __get__(self, obj, objtype=None):
        if obj is None or isinstance(obj, BaseElement):
            return self
        self.parent = obj.root
        return self

    def __set__(self, obj, value):
        if obj is None or isinstance(obj, BaseElement):
            return self
        self.parent = obj.root

    def pset(self, value):
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
                self._subby, _selector_dict[self._subby] % (self._subxpath, i)))
            for i, x in items
        ))

    @property
    def selected(self):
        for key in self.keys():
            element = self[key]
            if element.is_selected():
                yield key

import lxml.html


class BaseTableContainer(BaseContainer):

    thead = None
    tbody = None

    def _get_index_by_title(self, title):
        root = lxml.html.fromstring(self.thead.page_source)
        for idx, element in enumerate(root.xpath('//th')):
            if element.text_content().strip() == title:
                return idx + 1
        raise Exception('Title not Found!')

    def column(self, title=None, index=None):
        '''
        获取第N列的内容
        '''
        if title:
            idx = self._get_index_by_title(title)
        elif index:
            idx = index
        root = lxml.html.fromstring(self.tbody.page_source)
        return (e.text_content() for e in root.xpath('//tr/td[%d]' % (idx + 1)))

##########################################################################
#   其他


class MouseOverMixin(BaseContainer):

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


class LoginPage(BaseContainer):

    username = InputElement(By.XPATH, '//input[@id="username"]')
    password = InputElement(By.XPATH, '//input[@id="password"]')
    captcha = InputElement(By.XPATH, '//input[@name="captchaResponse"]')
    submit = InputElement(By.XPATH, '//input[@name="submit"]')
