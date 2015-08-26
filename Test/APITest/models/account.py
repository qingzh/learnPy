# -*- coding:utf-8 -*-

from APITest.models.models import APIType
from TestCommon.models.const import BLANK


GETACCOUNT = {"requestData": ["account_all"]}


class AccountInfoType(APIType):
    # 单条推广子链的数据类型
    __name__ = 'accountInfoType'

    def __init__(self, userId=BLANK, userName=BLANK, balance=BLANK, cost=BLANK,
                 payment=BLANK, budgetType=BLANK, budget=BLANK, regionTarget=BLANK,  excludeIp=BLANK, openDomains=BLANK,
                 regDomain=BLANK, userStat=BLANK,  weeklyBudget=BLANK):
        # ---------------------------------------------------------------------
        # 以下属性无法修改
        # long, Account ID
        self.userId = userId
        # string, Account Name
        self.userName = userName
        # double, Balance of Account
        self.balance = balance
        # double, Consume of Account
        self.cost = cost
        # int, Payment of Account, exclude Promotion
        # 账户总充值金额，不包括充值优惠
        self.payment = payment
        self.openDomains = openDomains
        self.regDomain = regDomain
        self.userStat = userStat
        self.weeklyBudget = weeklyBudget

        # ---------------------------------------------------------------------
        # 以下属性选填
        # int, 预算类型：0为不设置，1为日预算
        self.budgetType = budgetType
        # double, 账户预算, [10, 500000]
        self.budget = budget
        # string[], 推广低于列表，每个元素表示一个省
        self.regionTarget = regionTarget
        # string []
        self.excludeIp = excludeIp
