# -*- coding:utf-8 -*-s
from .models import APIType, APIData
from TestCommon.models.const import BLANK
from ..compat import is_sequence
import random
from APITest.compat import gen_chinese_unicode
from datetime import datetime

MAX_PRICE = 500000

__all__ = [
    'AdgroupType', 'CampaignId', 'AdgroupId']


class CampaignId(APIData):
    __name__ = 'campaignIds'

    def __init__(self, campaignIds=BLANK):
        self.campaignIds = is_sequence(campaignIds, True)


class AdgroupId(APIData):
    __name__ = 'adgroupIds'

    def __init__(self, adgroupIds):
        self.adgroupIds = is_sequence(adgroupIds, True)


class CampaignAdgroupId(APIType):
    __name__ = 'campaignAdgroupIds'

    def __init__(self, campaignId=BLANK, adgroupIds=BLANK):
        self.campaignId = campaignId
        self.adgroupIds = adgroupIds


class CampaignAdgroup(APIData):

    def __init__(self, campaignId=BLANK, adgroupTypes=BLANK):
        self.campaignId = campaignId,
        self.adgroupTypes = adgroupTypes

# amount of adgroups of a campaign is up to 2000

PLATFORM = [1, 2, 4, 3, 5, 6, 7]


class AdgroupType(APIType):
    __name__ = 'adgroupTypes'

    def __init__(self, adgroupId=BLANK, campaignId=BLANK, adgroupName=BLANK,
                 maxPrice=BLANK, negativeWords=BLANK, exactNegativeWords=BLANK,
                 pause=BLANK, status=BLANK, adPlatformOS=BLANK):
        # 分库分表： tb_unit_0003 (wolongtest)
        # 可不可以用SlotsDict ??
        # long, 对应SQL: id
        self.adgroupId = adgroupId
        # long, SQL: planid
        self.campaignId = campaignId
        # string, len<=30, i.e. 15个中文; SQL: name
        self.adgroupName = adgroupName
        # double, [0.3, 500000]; SQL: bid/100.0 存的是`分`
        self.maxPrice = maxPrice
        # string[]
        self.negativeWords = negativeWords
        # string[]
        self.exactNegativeWords = exactNegativeWords
        # boolean, default = False
        self.pause = pause
        # int, [0,1,2], 0: paused; 1: plan paused; 2:
        self.status = status
        # int, [1,2,4], 1:ios, 2:android; 4: o.w.
        self.adPlatformOS = adPlatformOS

    @classmethod
    def factory(cls, campaignId, amount=1):
        '''
        批量造 adgroupType
        @param amount: 整数，所需的单元总数
        @param campaignId: 所属计划ID
        '''
        # integer
        price = int(datetime.now().strftime('%I%M')) % 1000
        return list(cls(
            campaignId=campaignId,
            adgroupName=gen_chinese_unicode(30),
            maxPrice=price + random.random(),
            adPlatformOS=random.choice(PLATFORM),
        ) for i in range(amount))

    @classmethod
    def random(cls, **kwargs):
        price = int(datetime.now().strftime('%I%M')) % 1000
        default = dict(
            adgroupName=gen_chinese_unicode(30),
            maxPrice=price + random.random(),
            adPlatformOS=random.choice(PLATFORM),
        )
        default.update(kwargs)
        return cls(**default)

    def normalize(self, obj=None, **kwargs):
        if self._is_parent_instance(obj) or kwargs:
            obj = AdgroupType(**(obj or kwargs))
        else:
            obj = obj or self

        negativeWords = obj.get(
            'negativeWords', self.get('negativeWords', ['']))
        if '$' in negativeWords:
            negativeWords = ['']
        exactNegativeWords = obj.get(
            'exactNegativeWords', self.get('exactNegativeWords', ['']))
        if '$' in exactNegativeWords:
            exactNegativeWords = ['']
        price = round(float(obj.get('maxPrice', self.maxPrice)), 2)

        return AdgroupType(
            adgroupId=self.get('adgroupId', obj.get('adgroupId', None)),
            campaignId=self.campaignId,
            adgroupName=obj.get('adgroupName', self.adgroupName),
            maxPrice=price,
            negativeWords=negativeWords,
            exactNegativeWords=exactNegativeWords,
            pause=obj.get('pause', self.get('pause', False)),
            adPlatformOS=obj.get('adPlatformOS', self.adPlatformOS)
        )


def yield_adgroupTypes(n):
    for i in xrange(n):
        v = i % 3
        yield AdgroupType(
            adgroupName='adgroup_%d' % i,
            maxPrice=(i + 3) % MAX_PRICE / 10.0,
            negativeWords=['negative_%d' % i],
            exactNegativeWords=['exactNegative_%d' % i],
            pause=i & 0b1,
            status=v,  # invalid
            adPlatformOS=v + 1 if v != 2 else 4
        )
