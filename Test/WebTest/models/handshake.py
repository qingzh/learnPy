#! -*- coding:utf8 -*-


from ..compat import AttributeDict, BLANK, CustomProperty, AttributeDictWithProperty
import json


LEVEL_MAP = {
    'user': 1,
    'plan': 2,
    'unit': 3,
    'winfo': 4,
    'idea': 5,
    'app': 6,
    'phone': 7,
    'xiJin': 8,
    'ideaPro': 9,
    'ideaProPic': 10,
    'ideaProApp': 11}

class DateProperty(CustomProperty):

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        # 如果使用 obj[key] 就会进入死循环
        # 因为 obj.__setitem__ 对property进行了特殊处理
        # 应该是使用 dict.__setitem__
        return dict.__getitem__(obj, self._property_key)

    def __set__(self, obj, value):
        ''' type of obj: AttributeDict '''
        key = self._property_key
        if value == BLANK:
            return obj.pop(key, BLANK)
        if not isinstance(value, basestring):
            value = str(value)
        dict.__setitem__(obj, key, value)


class GenReport(AttributeDictWithProperty):

    '''
    JAVA:
    (long userId, ReportMergeType mergeType, Date startDate,
      Date endDate, Integer firstResult, Integer recordPerPage, ReportInfo rptInfo,
      AccountLevel level, AccountEntity userEntity, String orderName, Boolean orderValue)
    '''

    def __init__(self, level=BLANK, startDate=BLANK, endDate=BLANK, reportType=BLANK, recordPerPage=20, reqPageIndex=1, orderName=BLANK, orderValue=BLANK):
        super(GenReport, self).__init__(
            level=level,
            startDate=startDate,
            endDate=endDate,
            reportType=reportType,
            recordPerPage=recordPerPage,
            reqPageIndex=reqPageIndex,
            orderName=orderName,
            orderValue=orderValue),

    @property
    def level(self):
        return self['level']

    @level.setter
    def level(self, value):
        '''
        level 只能是基本类型（即不可能是字典等)
        所以直接使用 self['level'] 赋值即可
        '''
        if value == BLANK:
            return self.pop('level', BLANK)
        try:
            self['level'] = int(value)
        except ValueError:
            self['level'] = LEVEL_MAP.get(value)

    def set_order(self, orderName, orderValue):
        self.orderName = orderName
        self.orderValue = orderValue

    def date_wraps(key):
        def fget(self):
            return self[key]

        def fset(self, value):
            if value == BLANK:
                return self.pop(key, BLANK)
            if not isinstance(value, basestring):
                value = str(value)
            self[key] = value
        return fget, fset

    @property
    def uri(self):
        return '/cpc/report/reportAction/genReport.json'

    startDate = property(*date_wraps('startDate'))
    endDate = property(*date_wraps('endDate'))


class GenReportResponse(AttributeDict):
    __classhook__ = AttributeDict

    def __init__(self, *args, **kwargs):
        super(GenReportResponse, self).__init__(
            status=None,
            wolongError=None,
            data=None,
            extension=None)
        self.update(*args, **kwargs)


class CPCData(AttributeDictWithProperty):

    def property_wraps(key):
        def fget(self):
            return self[key]

        def fset(self, value):
            if not isinstance(value, basestring):
                try:
                    value = json.dumps(value)
                except TypeError:
                    pass
            self.__setitem__(key, value)
        return fget, fset

    where = property(*property_wraps('where'))
    context = property(*property_wraps('context'))


class Where(AttributeDictWithProperty):

    '''
    "where": {
      "filterFieldMap": {
        "startDate": "2015-05-15",
        "endDate": "2015-06-15",
        "level": "UserLevel",
        "planId": "",
        "unitId": ""
      },
      "recordPerPage": 20,
      "totalRecord": -1,
      "reqPageIndex": 5,
      "sortField": "clickRatio",
      "ascend": "true"
    }
    '''

    def __init__(self, *args, **kwargs):
        d = dict(*args, **kwargs)
        super(Where, self).__init__({
            "filterFieldMap": FilterFieldMap(),
            "recordPerPage": 20,
            "totalRecord": -1,
            "reqPageIndex": 1,
            "sortField": None,
            "ascend": None
        })
        self.update(d)


class FilterFieldMap(AttributeDictWithProperty):

    '''
    A python dict object:

    "filterFieldMap": {
        "startDate": "2015-05-15",
        "endDate": "2015-06-15",
        "level": "UserLevel",
        "planId": "",
        "unitId": ""
    }
    '''

    def __init__(self, startDate=BLANK, endDate=BLANK, level=BLANK, planId=BLANK, unitId=BLANK):
        super(FilterFieldMap, self).__init__(
            startDate=startDate, endDate=endDate, level=level, planId=planId, unitId=unitId)

    def __call__(self, *args, **kwargs):
        super(FilterFieldMap, self).update(*args, **kwargs)
