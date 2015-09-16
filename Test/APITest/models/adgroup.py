# -*- coding:utf-8 -*-s
from .models import APIType, APIData
from TestCommon.models.const import BLANK

MAX_PRICE = 500000

__all__ = [
    'AdgroupType', 'CampaignId']


class CampaignId(APIType):
    __name__ = 'campaignIds'

    def __init__(self, campaignIds=BLANK):
        self.campaignIds = campaignIds


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
