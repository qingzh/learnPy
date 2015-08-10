# -*- coding:utf-8 -*-

import json
from .map import yield_province_city
from .models import BaseData
from ..utils import yield_infinite
from datetime import datetime

# campaignId, status 是不可填的
campaignType_json = """
{
  "campaignId": 20379004,
  "campaignName": "1",
  "budget": 499999.99,
  "regionTarget": [
    "内蒙古"
  ],
  "excludeIp": [],
  "negativeWords": [
    "1:word1",
    "A"
  ],
  "exactNegativeWords": [
    "1:word2",
    "2"
  ],
  "schedule": [
    {
      "weekDay": 1,
      "startHour": 1,
      "endHour": 5
    },
    {
      "weekDay": 2,
      "startHour": 3,
      "endHour": 6
    }
  ],
  "showProb": 0,
  "pause": false,
  "status": 3
}
 """


def get_time(n):
    # 24*24=576
    n1 = n % 24
    n = n / 24
    n2 = n % 24
    n = n / 24
    return dict(
        weekDay=n % 7 + 1,
        startHour=min(n1, n2),
        endHour=max(n1, n2) + 1)


def get_ip(n):
    # 256进制
    ip_list = []
    while n > 0:
        ip_list.append(n & 255)
        n = n >> 8
    ip_list.extend([0, 0, 0, 0])
    if ip_list[3] == 0:
        ip_list[3] = 1
    return '.'.join((str(i) for i in ip_list[-3::-1]))


def get_ip(n):
    if n < 1000000:
        n = n + 1000000
    s = str(n)[::-1]
    s_list = [s[i:i + 2][::-1] for i in xrange(0, 8, 2)][::-1]
    return '.'.join(s_list)

MAX_BUDGET = 500000 - 10


def yield_campaignType(n=1):
    yield_city = yield_infinite(yield_province_city)
    salt = datetime.now().strftime('%Y%m%d%H%M%S%f')
    num = int(salt)
    for i in xrange(n):
        suffix = '%d_%s' % (i, salt)
        yield dict(
            # campaignId=num,
            campaignName='test%s' % suffix,
            budget=num % MAX_BUDGET + 10,
            regionTarget=[yield_city.next()],
            excludeIp=[get_ip(num)],
            negativeWords=['negative%s' % suffix],
            exactNegativeWords=['exactNegative%s' % suffix],
            schedule=[get_time(num)],
            showProb=num & 1,
            pause=num & 1 ^ 1,
            # status=num
        )
    yield_city.send(False)
