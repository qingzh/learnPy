# -*- coding:utf-8 -*-s
from .models import APIType, APIData, AttributeDict
from TestCommon.models.const import BLANK
from ..compat import is_sequence
import random
from APITest.compat import gen_chinese_unicode
from datetime import datetime

MAX_PRICE = 500000

__all__ = [
    'AdgroupType', 'CampaignId']


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
        # long
        self.adgroupId = adgroupId
        # long
        self.campaignId = campaignId
        # string, len<=30, i.e. 15 Chineses
        self.adgroupName = adgroupName
        # double, [0.3, 500000]
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
    def random(cls, campaignId, adgroupName=None):
        return cls(
            campaignId=campaignId,
            adgroupName=adgroupName or gen_chinese_unicode(30),
            maxPrice=int(datetime.now().strftime('%y%m%d')) + random.random(),
            adPlatformOS=random.choice(PLATFORM),
        )

    def normalize(self, obj=None):
        obj = obj or self
        negativeWords = obj.get(
            'negativeWords', self.get('negativeWords', ['']))
        exactNegativeWords = obj.get(
            'exactNegativeWords', self.get('exactNegativeWords', ['']))
        D = AdgroupType(
            adgroupId=self.adgroupId,
            campaignId=self.campaignId,
            adgroupName=obj.get('adgroupName', self.adgroupName),
            maxPrice=round(float(obj.get('maxPrice', self.maxPrice)), 2),
            negativeWords=negativeWords if '$' not in negativeWords else [''],
            exactNegativeWords=exactNegativeWords if '$' not in exactNegativeWords else [
                ''],
            pause=obj.get('pause', self.get('pause', False)),
            adPlatformOS=obj.get('adPlatformOS', self.adPlatformOS)
        )
        return D

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
