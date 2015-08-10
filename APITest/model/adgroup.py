# -*- coding:utf-8 -*-s
from .models import _slots_class

__all__ = ['CampaignAdgroupId', 'CampaignAdgroup', 'AdgroupType']

CampaignAdgroupId = _slots_class('CampaignAdgroupId', {
    "campaignId": None,
    "adgroupIds": None
})
CampaignAdgroup = _slots_class('CampaignAdgroup', {
    "campaignId": None,
    "adgroupTypes": None
})
# amount of adgroups of a campaign is up to 2000
AdgroupType = _slots_class('AdgroupType', [
    "adgroupId",  # long
    "campaignId",  # long
    "adgroupName",  # string, len<=30, i.e. 15 Chineses
    "maxPrice",  # double, [0.3, 500000]
    "negativeWords",  # string[]
    "exactNegativeWords",  # string[]
    "pause",  # boolean, default = False
    "status",  # int, [0,1,2], 0: paused; 1: plan paused; 2:
    "adPlatformOS",  # int, [1,2,4], 1:ios, 2:android; 4: o.w.
])

MAX_PRICE = 500000


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
