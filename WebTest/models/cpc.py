#! -*- coding:utf8 -*-

from .common import *
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

'''
怎么将NameEditContainer装配成InputElement
这两个是类似的：
    NameEditContainer. __set__ 就是设置文本,然后confirm
    NameEidtContainer. __get__ 就是获取文本
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


class NameEditContainer(BaseContainer):
    text = InputElement(By.CSS_SELECTOR, 'input.edit_text')
    confirm = InputElement(By.CSS_SELECTOR, 'input.edit_confirm')
    cancel = InputElement(By.CSS_SELECTOR, 'input.edit_cancel')

name_editor = ContainerElement(
    By.XPATH, './/input[@class="edit list-edit name"]',
    NameEditContainer(
        None, By.XPATH, '//div[@class="tableOpenWin"]/div[@class="inputBlank"]')
)


# 推广时段，列出了7天：周一 ... 周日
class DaysContainer(BaseContainer):

    header = ContainerElement(
        By.XPATH,
        './/ul[@class="timeWin-quick-ul"]',
        DictContainer, subxpath='.//li[@class]', subobj=InputElement
    )
    days = ContainerElement(
        By.XPATH,
        './/div[@class="win-c"]',
        DictContainer, subxpath='.//div[@class="time-data"]', subobj=InputElement
    )
    opts = ContainerElement(
        By.XPATH,
        './/div[@class="form-footer"]',
        DictContainer, subxpath='.//a[@class]', subobj=InputElement
    )


days_editor = ContainerElement(
    By.XPATH, './/input[@class="edit list-edit"]',
    DaysContainer(None, By.XPATH, './/div[@class="editTgsdWin"]')
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

add_plan_container = AddPlanContainer(
    None, By.XPATH, '//div[@class="addPlanWin"]')


# 自定义列，类似自定义区域？
class SelectorContainer(BaseContainer):
    header = ContainerElement(
        By.CLASS_NAME, 'select-title', DictContainer, sbuxpath='.//li[text() != ""]')
    content = ContainerElement(
        By.CLASS_NAME, 'select-content', DictContainer, sbuxpath='.//li[*/text() != ""]')

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


date_container = DateContainer(
    None, By.XPATH, '//div[@class="fn-date-container right"]')


class TRContainer(BaseContainer):

    '''
    怎么将checkbox这个属性变成TRContainer的属性
    __set__ ?
    '''
    checkbox = InputElement(By.XPATH, './/input[@type="checkbox"]')
    name = name_editor
    days = days_editor


class THContainer(BaseContainer):

    '''
    怎么将checkbox这个属性变成TRContainer的属性
    __set__ ?
    '''
    checkbox = InputElement(By.XPATH, './/input[@type="checkbox"]')
    # 名字，可以过滤
    # 可以排序

status_filter = DictContainer(
    None, By.XPATH, '//ul[@class="state-win"]', './/li', InputElement)

##########################################################################


class TabHeaderContainer(BaseContainer):
    # 新增
    add = ContainerElement(By.ID, 'addBtn', add_plan_container)
    # 批量操作
    batch = ContainerElement(By.ID, 'manyDo', batch_container)
    # 自定义列
    row_title = ContainerElement(By.ID, 'definRow', custom_row_container)
    # 选择日期
    date_picker = ContainerElement(
        By.XPATH, './/div[@class="input-append"]', date_container)
    # 过滤状态
    status = ContainerElement(
        By.CSS_SELECTOR, 'div.state-input input.state-btn', status_filter)


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
    '''
    all = ContainerElement(
        By.CSS_SELECTOR, 'input.allcheck',
        InputElement(By.XPATH, '//tr[@id="showAllRecords"]'))


class TabContainer(BaseContainer):

    """
    为什么要两层property?
    TODO: refactor

    或者能否保留 ContainerElement 这层的对象?
    意即：

    """
    __name__ = u'TAB主页面'

    # 页头：批量操作，选择时间，过滤状态灯
    header = ContainerElement(
        By.CSS_SELECTOR, 'div.main-nav-head',
        TabHeaderContainer)

    '''
    main-table-area 的话包含了tableOpenWin的控件
    也就是添加计划等的弹出窗口
    '''
    # 内容页
    table = ContainerElement(
        By.CSS_SELECTOR, 'div.main-table-area', TableContainer)


class CPCTabContainer(BaseContainer):
    # 标签栏：计划，单元，关键词，创意，附加创意
    tab = ContainerElement(
        By.CSS_SELECTOR, 'ul.main-nav-title',
        DictContainer, subxpath='./li', subobj=InputElement
    )
    # tab主页面
    body = ContainerElement(By.CLASS_NAME, 'main-nav-content', TabContainer)
    # 页数
    numbers = ListElement(By.CSS_SELECTOR, 'li.page-item')

    # 总记录数
    @property
    def allRecords(self):
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
        By.XPATH, '//body//div[@class="head"]', HeaderContainer)
    # 左侧树形图
    tree = ContainerElement(
        By.XPATH, './/body//div[@class="body-tree"]', TreeContainer)
    # 中间主页面
    body = ContainerElement(
        By.CSS_SELECTOR, 'div.body-main-area', CPCMainContainer)


class LoginPage(BasePage):

    username = InputElement(By.XPATH, '//input[@id="username"]')
    password = InputElement(By.XPATH, '//input[@id="password"]')
    captcha = InputElement(By.XPATH, '//input[@name="captchaResponse"]')
    submit = InputElement(By.XPATH, '//input[@name="submit"]')
