from ..compat import AttributeDict, BLANK
import json


class AttributeDictWithProperty(AttributeDict):

    def __init__(self, *args, **kwargs):
        """
        take care of nested dict
        """
        super(AttributeDict, self).__init__(*args, **kwargs)
        for key, value in self.iteritems():
            # Nested AttributeDict object
            # new object should be instance of self.__class__

            # compatible with `property`
            if isinstance(getattr(self.__class__, key), property):
                getattr(self.__class__, key).__set__(self, value)
            else:
                AttributeDictWithProperty.__setitem__(self, key, value)

    def __setitem__(self, key, value):
        if value == BLANK:
            # clear item
            return self.pop(key, BLANK)
        super(AttributeDictWithProperty, self).__setitem__(key, value)


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
