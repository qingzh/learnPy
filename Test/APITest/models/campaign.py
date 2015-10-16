# -*- coding:utf-8 -*-

import json
import logging
from .map import yield_province_city
from .models import AttributeDict
from ..utils import yield_infinite, chain_value
from ..compat import is_sequence, BLANK, gen_chinese_unicode
from datetime import datetime
import collections

# campaignId, status 是不可填的
from .models import APIType, APIData
from .wrappers import *

log = logging.getLogger(__name__)

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


__all__ = [
    'CampaignId', 'Schedule', 'CampaignType', 'schedule_wrapper']


def budget_wrapper(value):
    '''
    设为0，表示不限制预算(数据库填"-1")
    需不需要转化为2位小数的字符串，以方便比较
    '''
    try:
        value = round(float(value), 2)
    except Exception:
        return value
    if abs(value-0) < 0.00000001:
        return -1
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


def schedule_escape(value):
    '''
    将 "110-117" 转化为 Schedule(weekDay=1, startHour=10, endHour=17) 
    '''
    if value is None or value is BLANK:
        return value
    # Schedule，则返回[value]
    if isinstance(value, dict):
        return [value]
    # 字符串，则转化为数组
    if isinstance(value, basestring):
        value = [value]
    # 数组：如果是Schedule数组，则直接返回
    if isinstance(value[0], dict):
        return value
    # 现在 value 应该是字符串数组
    schedule = []
    for item in value:
        # 110-117
        s = [x.strip() for x in item.split('-')]
        weekday, startHour, endHour = s[0][0], s[0][1:], s[1][1:]
        schedule.append(Schedule(weekday, startHour, endHour))
    return schedule


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

    def __setitem__(self, key, value):
        # 如果是 schedule 则进行转义，否则正常赋值
        if key == 'schedule':
            value = schedule_escape(value)
        super(CampaignType, self).__setitem__(key, value)


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
            regionTarget=chain_value(
                obj, self, 'regionTarget', [], region_wrapper),
            excludeIp=chain_value(
                obj, self, 'excludeIp', [''], set_wrapper),
            negativeWords=chain_value(
                obj, self, 'negativeWords', [''], set_wrapper),
            exactNegativeWords=chain_value(
                obj, self, 'exactNegativeWords', [''], set_wrapper),
            schedule=chain_value(
                obj, self, 'schedule', DEFAULT_SCHEDULE, schedule_wrapper),
            showProb=chain_value(obj, self, 'showProb', 0),
            pause=chain_value(obj, self, 'pause', False),
            status=chain_value(obj, self, 'status', BLANK),
        )

    def __eq__(self, obj):
        '''
        需要特殊处理的字段： 
        status 字段忽略
        budget 字段进行四舍五入的比较(round(float, 2))，这个在wrapper里面就做了
        '''
        if not isinstance(obj, collections.Mapping):
            return False
        for key in self.iterkeys():
            if key == 'status':
                continue
            base, expt = self[key], obj[key]
            '''序列类型：转化为集合； 其他类型：直接比较'''
            if is_sequence(base):
                if is_sequence(expt) and not set(base)-set(expt):
                    continue
                # else: return False
            else:
                if base == expt:
                    continue
                # else: return False
            log.debug('key: %s, %s != %s', key, base, expt)
            # raise AssertionError('key: %s, %s != %s' % (key, base, expt))
            return False
        return True

    def db_row(self):

        return 'id, name, budget, region, ipblack, negative_word, '\
            'negative_query, period, idea_show_mode, is_paused'

