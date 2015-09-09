#! -*- coding:utf8 -*-

from .common import *
from ..compat import By, WebElement
import collections

'''
怎么将NameEditContainer装配成InputElement
这两个是类似的：
    NameEditContainer. __set__ 就是设置文本,然后confirm
    NameEidtContainer. __get__ 就是获取文本


TODO:
控件的测试，写在控件类里？

TODO:
Nested Element??

'''


##########################################################################

'''
这里没法用DictContainer做批量
因为有AlertElement
'''


class BatchBudgetContainer(BaseContainer):
    chooses = ListElement(By.XPATH, './/p', InputElement)
    buttons = ListElement(By.XPATH, './/a[@class]', InputElement)


class BatchContainer(BaseContainer):

    suspend = AlertElement(
        By.XPATH, '//li[contains(@class, "stop-promotion")]')
    # resume = ClickElement(By.CSS_SELECTOR, 'li.start-promotion')
    resume = AlertElement(
        By.XPATH, '//li[contains(@class, "start-promotion")]')
    budget = ContainerElement(
        By.XPATH, '//li[contains(@class, "modify-budget")]',
        BatchBudgetContainer
    )
    '''
    price = ContainerElement(
        By.XPATH, '//li[contains(@class, "modify-price")]',
        )
    match_pattern = ClickElement(
        By.XPATH, '//li[contains(@class, "match_pattern")]')
    '''
    delete = AlertElement(By.CSS_SELECTOR, 'li.delete-item')


# 批量操作
# TODO: 这里需要修改，有些事AlertElement, 不是InputElement
batch_container = DictContainer(
    None, By.XPATH, '//div[contains(@class, "plcz-ul")]', './/li/a', InputElement)
batch_container = BatchContainer(
    None, By.XPATH, '//div[contains(@class, "plcz-ul")]')


# 修改名字


class TextEditContainer(BaseContainer):
    text = InputElement(By.CSS_SELECTOR, 'input.edit_text')
    confirm = InputElement(By.CSS_SELECTOR, 'input.edit_confirm')
    cancel = InputElement(By.CSS_SELECTOR, 'input.edit_cancel')

    def set_and_confirm(self, value):
        self.text = value
        self.confirm = True

    def set_and_cancel(self, value):
        self.text = value
        self.cancel = True

'''
让get方法只是获取值
不单击 input button
可以吗
怎么动态定义?
单元级别下，可以修改的是unitName，显示的是unitName
由于每个level只有一个可以编辑的名字
'''
name_editor = ContainerElement(
    By.XPATH, './/td[@name][contains(@class,"editable")]//input[contains(@class, "name")]',
    TextEditContainer(
        None, By.XPATH, '//div[@class="tableOpenWin"]/div[@class="inputBlank"]')
)

budget_editor = ContainerElement(
    By.XPATH, './/td[@name="bid" or @name="budget"]//input',
    TextEditContainer(
        None, By.XPATH, '//div[@class="tableOpenWin"]/div[@class="inputBlank"]')
)

platform_editor = ContainerElement(
    By.CSS_SELECTOR, 'td[name="platform"] input.edit',
    DictContainer(
        None, By.XPATH, '//div[@class="openwin-box"]', subxpath='.//input | .//a',
        key=lambda x: x.text.strip() or x.find_element(By.XPATH, '..').text.strip())
)

status_editor = StatusElement(
    By.CSS_SELECTOR, 'span.icon-state',
    key=lambda x: x.get_attribute('class').rpartition(' ')[-1],
    key_map={u'暂停': 'pause', u'恢复': 'run'})

order_editor = StatusElement(
    By.CSS_SELECTOR, 'span.order',
    key=lambda x: x.get_attribute('class').rpartition(' ')[-1],
    key_map={u'升序': 'order-up', u'降序': 'order-down'})

# 推广时段，列出了7天：周一 ... 周日


class DaysContainer(BaseContainer):

    days = DictElement(
        By.XPATH, './/li[contains(@class,"timeWin-quick-item")] | .//div[contains(@class,"time-data")]/div[@class="timeWin-th"]',
        subobj=InputElement,
        key=lambda x: x.text.strip('"')
    )
    opts = ContainerElement(
        By.XPATH,
        './/div[@class="form-footer"]',
        DictContainer, subxpath='.//a[@class]', subobj=InputElement
    )

    def clear(self):
        for key in self.days.iterkeys():
            self.days[key] = False

    def set_and_confirm(self, _list):
        '''
        这是一个复选框，未选择的要清除
        '''
        # Be aware of `basestring`
        if not isinstance(_list, collections.MutableSequence):
            _list = [_list]
        for i in _list:
            if i not in self.days:
                self.days[i] = False
            else:
                self.days[i] = True
        self.opts[u'确定'] = True

    def set(self, _list):
        '''
        只进行复选
        '''
        if not isinstance(_list, collections.MutableSequence):
            _list = [_list]
        for i in _list:
            if i in self.days:
                self.days[i] = True

    def get_selected(self, key=None):
        '''
        @return list of selected items
        '''
        l = []
        for k in self.days.iterkeys():
            if self.days[k].is_selected():
                (key or l.append(k)) and l.append(key(self.days[k]))
        return l


days_editor = ContainerElement(
    By.XPATH, './/td[@name="period"]//input[@type="button"]',
    DaysContainer(None, By.XPATH, '//div[@class="editTgsdWin"]')
)


# 添加计划
class AddPlanContainer(BaseContainer):

    '''
    新增计划的Form类
    '''
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


# 单元
class AddUnitContainer(BaseContainer):

    '''
    新增计划的Form类
    '''
    '''
    plan这里，因为对find_elements做了过滤，只显示is_displayed的……
    所以只用WebElement.find_elements有问题
    '''
    plan = ContainerElement(
        By.TAG_NAME, 'select',
        DictContainer(
            None, By.XPATH, '.', subxpath='./option', subobj=InputElement)
    )
    name = InputElement(
        By.XPATH, './/input[@id="unitName"]')
    # `radio`
    unitBid = InputElement(
        By.XPATH, './/input[@id="unitBid"]')
    platform = ContainerElement(
        By.CSS_SELECTOR, 'p.addUnitForm-row',
        DictContainer, subxpath='./input',
        key=lambda x: x.text.strip() or x.find_element(By.XPATH, '..').text.strip())
    opts = ContainerElement(
        By.CSS_SELECTOR, 'div.form-footer',
        DictContainer, subxpath='./a[@class]', subobj=InputElement)

add_plan_container = AddPlanContainer(
    None, By.XPATH, '//div[@class="addPlanWin"]')

add_unit_container = AddUnitContainer(
    None, By.XPATH, '//div[@class="addUnitWin"]')


# 自定义列，类似自定义区域？
class SelectorContainer(BaseContainer):
    header = ContainerElement(
        By.CLASS_NAME, 'select-title',
        DictContainer, subxpath='.//li[text() != ""]', subobj=InputElement)
    content = ContainerElement(
        By.CLASS_NAME, 'select-content',
        DictContainer, subxpath='.//li[*/text() != ""]', subobj=InputElement)
    confirm = InputElement(By.CSS_SELECTOR, 'a.columnSave')
    cancel = InputElement(By.CSS_SELECTOR, 'a.columnCancel')

    def select_all(self):
        self.header[u'全部'] = True
        self.confirm = True

custom_row_container = SelectorContainer(
    None, By.XPATH, '//div[contains(@class, "columnWin")]')


'''
和 推广区域 等 控件 类似
左上角有快捷按钮：默认/全部/自定义
然后就是 InputElement 数组
可能有 确认/取消 等按钮

'''

# 选择日期


class DateContainer(BaseContainer):

    '''
    Date format: '2015-01-01'
    >>> date = DateContainer(parent, by, locator)
    >>> date.start_date = '2015-01-01'
    >>> date.header.get(u'本月').click()
    '''

    header = ContainerElement(
        By.XPATH, './/div[@class="fast-link"]', DictContainer)
    start_date = InputElement(By.CSS_SELECTOR, 'div.fn-date-left input')
    end_date = InputElement(By.CSS_SELECTOR, 'div.fn-date-right input')
    confirm = InputElement(By.CSS_SELECTOR, 'a.confirm-btn')
    cancel = InputElement(By.CSS_SELECTOR, 'a.close-btn')

    def set_date(self, start, end):
        self.start_date = start
        self.end_date = end
        self.confirm = True

    def set_header(self, value):
        self.header = value
        self.confirm = True

date_container = DateContainer(
    None, By.XPATH, '//div[@class="fn-date-container right"]')

question_mark = BaseElement(By.CSS_SELECTOR, 'body > div.helpBlank')


class TRContainer(BaseContainer):

    '''
    怎么将checkbox这个属性变成TRContainer的属性
    __set__ ?
    '''
    checkbox = InputElement(By.XPATH, './/input[@type="checkbox"]')
    unitName = InputElement(By.XPATH, './/td[@name="unitName"]//a')
    planName = InputElement(By.XPATH, './/td[@name="planName"]//a')
    status = BaseElement(By.CSS_SELECTOR, 'span.text-state')
    bid = BaseElement(By.XPATH, './/td[@name="bid"]')
    negWord = BaseElement(By.XPATH, './/td[@name="negWord"]')
    platform = BaseContainer(By.XPATH, './/td[@name="platform"]')
    name_editor = name_editor
    status_editor = status_editor
    days_editor = days_editor
    platform_editor = platform_editor
    budget_editor = budget_editor

    @property
    def status(self):
        return self.root.find_element(By.CSS_SELECTOR, 'span.text-state').text


class THContainer(BaseContainer):

    '''
    怎么将checkbox这个属性变成TRContainer的属性
    __set__ ?
    '''
    checkbox = InputElement(By.XPATH, './/input[@type="checkbox"]')
    # 名字，可以过滤
    filter = DictElement(
        By.XPATH, './/a[contains(@class, "filter")]',
        subobj=InputElement, key=lambda x: x.find_element(By.XPATH, '..').text)

    # 可以排序
    order = DictElement(
        By.XPATH, './/span[contains(@class, "order")]',
        subobj=kwargs_dec(
            StatusElement,
            key=lambda x: x.get_attribute('class').rpartition(' ')[-1],
            key_map={u'升序': 'order-up', u'降序': 'order-down'}),
        key=lambda x: x.find_element(By.XPATH, '..').text.strip())

    # 问号
    question = DictElement(
        By.XPATH, './/td//img',
        subobj=kwargs_dec(ContainerElement, obj=BaseElement(
            By.XPATH, '//body/div[contains(@class, "helpBlank")]')),
        key=lambda x: x.find_element(By.XPATH, '..').text.strip())


##########################################################################


class DynamicContainerElement(ContainerElement):

    def __init__(self, by, locator, obj, *args, **kwargs):
        '''
        obj is a function: func(WebElement)
        return target container object type
        '''
        # 注意，`super` 这里是ContainerElemeng, 不是 DynamicContainerElement
        super(ContainerElement, self).__init__(by, locator)
        self._obj_func = obj
        self._args_ = args
        self._kwargs_ = kwargs

    def __get__(self, obj, objtype=None):
        # 注意，`super` 这里是ContainerElemeng, 不是 DynamicContainerElement
        root = super(ContainerElement, self).__get__(obj, objtype)
        obj_hook = self._obj_func(root)
        if type(obj_hook) is type:
            self._container_ = obj_hook(root, *self._args_, **self._kwargs_)
        else:
            self._container_ = obj_hook
        if hasattr(self._container_, '__get__'):
            return self._container_.__get__(root)
        self._container_.parent = root
        return self._container_


status_filter = DictContainer(
    None, By.XPATH, '//div[@id="tool-btns"]//ul[@class="state-win"]', subxpath='./li', subobj=InputElement)


class TabHeaderContainer(BaseContainer):
    _add_dict = {
        u'添加单元': add_unit_container,
        u'添加计划': add_plan_container,
    }
    # 新增
    add = DynamicContainerElement(
        By.ID, 'addBtn',
        obj=lambda x: TabHeaderContainer._add_dict.get(x.text))
    # 批量操作
    batch = ContainerElement(By.ID, 'manyDo', batch_container)
    # 自定义列
    row_title = ContainerElement(By.ID, 'definRow', custom_row_container)
    # 选择日期
    date = ContainerElement(
        By.XPATH, './/div[@class="input-append"]', date_container)
    # 过滤状态
    status = ContainerElement(
        By.CSS_SELECTOR, 'div#tool-btns input.state-btn', status_filter)


class TableContainer(BaseContainer):
    thead = ContainerElement(
        By.XPATH, './/thead/tr', THContainer)
    tbody = ListElement(
        By.XPATH, './/tbody/tr[not(@id) or @id!="showAllRecords"]', subobj=TRContainer)

    '''
    TODO:
    这样联动设计导致的后果就是：
      当调用 .all 的时候 thead会默认被勾上，意即单页全选
    但是 .all = False 并不会取消单页全选，所以……
    我搅得，这里有待商榷！

    TODO:
       可能不存在 all 选项！
    '''
    all = ContainerElement(
        By.CSS_SELECTOR, 'input.allcheck',
        InputElement(By.XPATH, '//tr[@id="showAllRecords"]'))

##########################################################################

"""
为什么要两层property?
TODO: refactor

或者能否保留 ContainerElement 这层的对象?
"""


class CPCPageNumberContainer(BaseContainer):
    recordPerPage = ContainerElement(
        By.XPATH, './/div[@class="page-num"]/select',
        DictContainer(
            None, By.XPATH, './option', subxpath='../option', subobj=InputElement, visible=False)
    )
    number_list = ListElement(By.XPATH, './/li[contains(@class,"page-item")]')
    number_turn = InputElement(By.XPATH, './/li[@class="page-turn"]//input')
    confirm_turn = InputElement(By.XPATH, './/li[@class="page-turn"]//a')

    def set_number(self, value):
        self.number_turn = value
        self.confirm_turn = True


class StyleContainerElement(ContainerElement):

    def __get__(self, obj, objtype=None):
        if obj.root.find_element(self.by, self.locator).size['height'] == 0:
            if self.locator == 'div.sub-nav-cont':
                self.locator = 'div.sub-nav-cont2'
            else:
                self.locator = 'div.sub-nav-cont'
        return super(StyleContainerElement, self).__get__(obj, objtype)


class CPCTabContainer(BaseContainer):
    # 标签栏：计划，单元，关键词，创意，附加创意
    level = ContainerElement(
        By.CSS_SELECTOR, 'ul.main-nav-title',
        DictContainer, subxpath='./li', subobj=InputElement
    )
    # tab主页面

    # 选择类型
    style = StyleContainerElement(
        By.CSS_SELECTOR, 'div.sub-nav-cont',
        DictContainer, subxpath='.//li', subobj=InputElement)

    # 页头：批量操作，选择时间，过滤状态灯
    tools = ContainerElement(
        By.CSS_SELECTOR, 'div.main-nav-head',
        TabHeaderContainer)

    '''
    main-table-area 的话包含了tableOpenWin的控件
    也就是添加计划等的弹出窗口
    '''
    # 内容页
    table = ContainerElement(
        By.CSS_SELECTOR, 'div.main-table-area', TableContainer)

    # 页数
    number = ContainerElement(
        By.XPATH, './/div[@class="page-area"]',
        CPCPageNumberContainer
    )
    '''
    这里有一个问题，selector是很难定义点击之后显示的。
    因为他本来就是显示的……因为他需要点击的父亲结点是<select>
    <select>
        <option> A </option>
    </select>
    '''
    # 总记录数
    @property
    def pageInfo(self):
        root = self.root
        if isinstance(root, WebElement):
            root = root.parent
        return PageInfo(root.execute_script('return pageArea.getData()'))


class CPCMainContainer(BaseContainer):

    '''
    CPC主页面
    '''
    # 当前位置
    position = ContainerElement(
        By.CSS_SELECTOR, 'div.main-local',
        ListContainer, subxpath='./a[@class]', subobj=InputElement
    )
    # 可以将info做成DictContainer, 以x.text.split(':')[0].strip()为key
    '''
    TODO: 这些控件如何做一个映射?
    是选出可见的控件，然后用mapping做对应？
    还是直接将所有控件封装，然后调用（不管是否可见），因为测试的时候是否课件是由你来决定的~
    '''
    # 当前位置的 信息
    # 例如，当前在账户下，则显示账户信息
    # 		当前在计划下，则显示计划信息
    info = ContainerElement(
        By.CSS_SELECTOR, 'div.main-info',
        ListContainer, subxpath='./div[@class]', subobj=BaseElement
    )
    # Tab页面
    main = ContainerElement(
        By.CSS_SELECTOR, 'div.main-nav.head-tab',
        CPCTabContainer
    )


class HeaderContainer(BaseContainer):

    '''
    CPC系统页头，应该所有系统都是一致的？
    '''
    header = ContainerElement(
        By.XPATH, './/ul[@class="head-nav"]',
        DictContainer, subxpath='./li/a', subobj=InputElement)


class TreeContainer(BaseContainer):

    '''
    CPC系统左侧树形图
    '''
    title = InputElement(By.CSS_SELECTOR, 'div.tree-title')
    list = ContainerElement(
        By.CSS_SELECTOR, 'ul.level1', ListContainer, subxpath='./li', subobj=InputElement)


class CPCPage(BasePage):
    # 如果用ContainerElement
    # 则刷新页面之后，这个属性就废了！！！！

    # 如果在__init__初始化，就不能动态设置属性了！
    # self.header = ContainerElement(
    #     By.XPATH, '//body//div[@class="head"]', HeaderContainer)

    # 页头
    banner = ContainerElement(
        By.CSS_SELECTOR, 'body div.head', HeaderContainer)
    # 左侧树形图
    tree = ContainerElement(
        By.XPATH, './/body//div[@class="body-tree"]', TreeContainer)
    # 中间主页面
    body = ContainerElement(
        By.CSS_SELECTOR, 'div.body-main-area', CPCMainContainer)
