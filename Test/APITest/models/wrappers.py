# -*- coding:utf-8 -*-

from ..compat import is_sequence

__all__ = [
    'schedule_wrapper', 'set_wrapper', 'budget_wrapper', 'region_wrapper']

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


def schedule_wrapper(value):
    if not is_sequence(value):
        return value
    if len(value) == 1 and value[0]['weekDay'] == 0:
        return DEFAULT_SCHEDULE
    return value


# 格式化(精确)否定关键词
def set_wrapper(value):
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
        value = [value]
    if [u'所有地域'] == value:
        return [u'所有地域']
    return value