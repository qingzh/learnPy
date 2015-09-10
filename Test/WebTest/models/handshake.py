#! -*- coding:utf8 -*-


from ..compat import AttributeDict, BLANK
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


class AttributeDictWithProperty(AttributeDict):

    '''
    允许设置字典的property
    property属性通过 __setattribute__ 调用
    property方法里调用 同样名称的元素 (__item__)
    '''

    def __init__(self, *args, **kwargs):
        """
        take care of nested dict
        """
        super(AttributeDict, self).__init__(*args, **kwargs)
        for key in self.keys():
            # Nested AttributeDict object
            # new object should be instance of self.__class__

            # compatible with `property`
            value = self[key]
            if isinstance(getattr(self.__class__, key, None), property):
                getattr(self.__class__, key).__set__(self, value)
            else:
                AttributeDictWithProperty.__setitem__(self, key, value)

    def __setitem__(self, key, value):
        if value == BLANK:
            # clear item
            return self.pop(key, BLANK)
        super(AttributeDictWithProperty, self).__setitem__(key, value)


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
