# -*- coding:utf-8 -*-

import json
from .map import yield_province_city
from .models import AttributeDict
from ..utils import yield_infinite, chain_value
from ..compat import is_sequence, BLANK, gen_chinese_unicode
from datetime import datetime
import collections

# campaignId, status 是不可填的
from .models import APIType, APIData


# 推广时段默认值
DEFAULT_SCHEDULE = [
    {"weekDay": 1, "startHour": 0, "endHour": 24},
    {"weekDay": 2, "startHour": 0, "endHour": 24},
    {"weekDay": 3, "startHour": 0, "endHour": 24},
    {"weekDay": 4, "startHour": 0, "endHour": 24},
    {"weekDay": 5, "startHour": 0, "endHour": 24},
    {"weekDay": 6, "startHour": 0, "endHour": 24},
    {"weekDay": 7, "startHour": 0, "endHour": 24},
]

# 格式化推广时段


def schedule_wrapper(value):
    if not is_sequence(value):
        return value
    if len(value) == 1 and value[0]['weekDay'] == 0:
        return DEFAULT_SCHEDULE
    return value


# 格式化(精确)否定关键词
def negwords_wrapper(value):
    if not is_sequence(value):
        return value
    # length: 1; items: '$'
    if ['$'] == value:
        return ['']
    return value


def budget_wrapper(value):
    try:
        return round(float(value), 2)
    except Exception:
        return value


def region_wrapper(value):
    if not is_sequence(value):
        return value
    if [u'所有地域'] == value:
        return [u'所有地域']
    return value


class CampaignId(APIData):
    __name__ = 'campaignIds'

    def __init__(self, campaignIds=BLANK):
        self.campaignIds = is_sequence(campaignIds, True)


class Schedule(APIData):

    def __init__(self, weekDay=BLANK, startHour=BLANK, endHour=BLANK):
        self.weekDay = weekDay
        self.startHour = startHour
        self.endHour = endHour


class CampaignType(APIType):
    __name__ = 'campaignTypes'

    def __init__(self, campaignId=BLANK, campaignName=BLANK, budget=BLANK,
                 regionTarget=BLANK, excludeIp=BLANK, negativeWords=BLANK,
                 exactNegativeWords=BLANK, schedule=BLANK, showProb=BLANK,
                 pause=BLANK, status=BLANK):
        # 分库分表： tb_plan_0003 (wolongtest)
        # 可不可以用SlotsDict ??
        # long, 对应SQL: id
        # auto, `id`
        self.campaignId = campaignId
        # string, len<=30, i.e. 15个中文; SQL: name
        # required `name`
        self.campaignName = campaignName
        # double, [10, 500000]; SQL: bid/100.0 存的是`分`
        # default null, `budget`
        self.budget = budget
        # string[]
        # default null, `region`
        self.regionTarget = regionTarget
        # string[]
        # default null, `ipblack`
        self.excludeIp = excludeIp
        # string[]
        # default null, `negative_word`
        self.negativeWords = negativeWords
        # string[]
        # default null, `negative_query`
        self.exactNegativeWords = exactNegativeWords
        # ScheduleType[]
        # default null, `period`
        self.schedule = schedule
        # showProb: [0,1], default 0
        # default 0, `idea_show_mode`
        self.showProb = showProb
        # boolean
        # default = False, `is_paused`
        self.pause = pause
        # int, [0,1,2,3,4]
        # 0计划暂停，1账户预算不足，2计划预算不足，3暂停时段，4推广中
        # invalid
        self.status = status

    @classmethod
    def factory(cls, amount=1):
        '''
        批量造 adgroupType
        @param amount: 整数，所需的单元总数
        @param campaignId: 所属计划ID
        '''
        # integer
        return list(cls(
            campaignName=gen_chinese_unicode(30),
        ) for i in range(amount))

    @classmethod
    def random(cls, **kwargs):
        kwargs.setdefault(
            "campaignName", gen_chinese_unicode(30)
        )
        return cls(**kwargs)

    def normalize(self, obj=None, **kwargs):
        '''
        obj(**kwargs) or self
        '''
        if obj:
            obj = obj(**kwargs)
        elif kwargs:
            obj = CampaignType(**kwargs)
        else:
            obj = self

        return CampaignType(
            campaignId=chain_value(self, obj, 'campaignId', None),
            campaignName=chain_value(obj, self, 'campaignName', BLANK),
            budget=chain_value(obj, self, 'budget', -1, budget_wrapper),
            regionTarget=chain_value(obj, self, 'regionTarget', []),
            excludeIp=chain_value(
                obj, self, 'excludeIp', [''], negwords_wrapper),
            negativeWords=chain_value(
                obj, self, 'negativeWords', [''], negwords_wrapper),
            exactNegativeWords=chain_value(
                obj, self, 'exactNegativeWords', [''], negwords_wrapper),
            schedule=chain_value(
                obj, self, 'schedule', DEFAULT_SCHEDULE, schedule_wrapper),
            showProb=chain_value(obj, self, 'showProb', 0),
            pause=chain_value(obj, self, 'pause', False),
            status=chain_value(obj, self, 'status', BLANK),
        )

    def __eq__(self, obj):
        if not isinstance(obj, collections.Mapping):
            return False
        for key in self.iterkeys():
            if key == 'status':
                continue
            if self[key] != obj[key]:
                return False
        return True

    def db_row(self):

        return 'id, name, budget, region, ipblack, negative_word, '\
            'negative_query, period, idea_show_mode, is_paused'

