# -*- coding:utf-8 -*-

import logging
import collections
from APITest.models.models import APIType
from TestCommon.models.const import BLANK
from .wrappers import *
from ..utils import chain_value

log = logging.getLogger(__name__)
__all__ = ['GETACCOUNT', 'AccountType']

GETACCOUNT = {"requestData": ["account_all"]}

class AccountType(APIType):
    # 单条推广子链的数据类型
    __name__ = 'accountInfoType'

    def __init__(self, userId=BLANK, userName=BLANK, balance=BLANK, cost=BLANK,
                 payment=BLANK, budgetType=BLANK, budget=BLANK, 
                 openDomains=BLANK,
                 regionTarget=BLANK,  excludeIp=BLANK, regDomain=BLANK,
                 userStat=BLANK,  weeklyBudget=BLANK):
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
        # openDomains 没有用了
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

    def normalize(self, obj=None, **kwargs):
        '''
        obj(**kwargs) or self
        '''
        if obj:
            obj = obj(**kwargs)
        elif kwargs:
            obj = AccountType(**kwargs)
        else:
            obj = self

        budgetType=chain_value(obj, self, 'budgetType', BLANK) 
        if str(budgetType) == '0':
            budget = 0
        else:
            budget = chain_value(obj, self, 'budget', BLANK, budget_wrapper)

        return AccountType(
            userId=chain_value(self, obj, 'userId', BLANK),
            userName=chain_value(self, obj, 'userName', BLANK),
            balance=chain_value(self, obj, 'balance', BLANK),
            cost=chain_value(self, obj, 'cost', BLANK),
            payment=chain_value(self, obj, 'payment', BLANK),
            openDomains=chain_value(self, obj, 'openDomains', BLANK),
            regDomain=chain_value(self, obj, 'regDomain', BLANK),
            userStat=chain_value(self, obj, 'userStat', BLANK),
            weeklyBudget=chain_value(self, obj, 'weeklyBudget', BLANK),
            budgetType=int(budgetType),
            budget=budget,
            regionTarget=chain_value(                
                obj, self, 'regionTarget', [], region_wrapper),
            excludeIp=chain_value(
                obj, self, 'excludeIp', [''], set_wrapper),
        )
