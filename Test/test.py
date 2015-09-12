from TestCommon import AttributeDictWithProperty, BLANK, CustomProperty


class DateProperty(CustomProperty):

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        return dict.__getitem__(obj, self._property_key)

    def __set__(self, obj, value):
        dict.__setitem__(obj, self._property_key, value)


class C(AttributeDictWithProperty):
    abc = DateProperty('abc')

c = C()
c['abc'] = 123
try:
    c.abc = 456
except Exception:
    pass
print getattr(c, 'abc')
