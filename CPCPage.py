#! -*- coding:utf8 -*-


from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import time
from selenium.common.exceptions import NoSuchElementException

"""
CPC
|-- Tab
     | -- $(".tool-btns").find(".button"), './/[contains(@class, "button")]'




Button Actions:
{ key: container() }
key = button id
(x.id: x)

http://www.w3schools.com/html/html_form_input_types.asp


"""
# 新增计划
add_button = (By.XPATH, './/a[@id="addBtn"]')
add_plan = (By.XPATH, '//div[@class="addPlanWin"]')

# 日期选择
date_button = (By.XPATH, './/div[@class="fn-dates-picker"]')
date_selector = (By.XPATH, './/div[@class="fn-dates-container"]')
# 状态筛选
state_button = (By.XPATH, './/div[@class="state-input"]')
# state_button.input(not @readonly)
state_filter = (By.XPATH, '//ul[@class="state-win"]')

# 修改名称
name = (By.XPATH, './/div[@class="inputBlank"]')

# 修改预算
budget = (By.XPATH, './/div[@class="inputBlank-myrs"]')
batch_budget = (By.XPATH, './/div[@class="blank-main"]')

# 推广时段
days = (By.XPATH, './/div[@class="editTgsdWin"]')


class NameEditContainer(BaseContainer):
    text = InputElement(By.XPATH, './/input[@class="edit_text"]')
    confirm = InputElement(By.XPATH, './/input[@class="edit_confirm"]')
    cancel = InputElement(By.XPATH, './/input[@class="edit_cancel"]')

name_editor = NameEditContainer(
    None, By.XPATH, '//div[@class="tableOpenWin"]/div[@class="inputBlank"]')
