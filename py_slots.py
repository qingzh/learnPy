#
class A(object):
    aa = 0
    __slots__ = ['a']

    def __init__(self):
        self.__class__.__slots__ = ['a0', 'a1']
        self.a0 = '0'
        self.a1 = '1'


class B(A):
    bb = 1
    __slots__ = ['b']


class C(object):
    cc = 2
    #__slots__ = ['c']


class BC(B, C):
    bc = 3
    __slots__ = ['bc']


class F(object):
    ff = 4
    __slots__ = ['f']


'''
IMpossible to set __slots__ in a instance
'''


class G(object):
    gg = 5

    def set_readonly(self):
        self.__dict__ = dict(g=NOne, g0=None, g1=None)
        self.__slots__ = []  # FAILED

'''
make __dict__ read-only after initiated
e.g. locked attributes
'''


class H(object):

    def __init__(self):
        self.abc = 1

    ''' failed "maximum recursion depth exceed"
    @property
    def __dict__(self):
        if hasattr(self, '__frozendict__') is False:
            self.__frozendict__ = self.__dict__
        return self.__frozendict__
    '''
    '''
    def __setattr__(self, key, value):
        if 'key' == '__dict__':
            return AttributeError
    '''


class AutoSlots(type):

    def __new__(cls, name, bases, dct):
        slots = dict.fromkeys(dct.get('__slots__', []))
        if '__init__' in dct:
            init = dct['__init__']
            ifvn = init.func_code.co_varnames
            for i in xrange(init.func_code.co_argcount):
                x = ifvn[i]
                if x[:1] == '_':
                    slots[x[1:]] = None
        dct['__slots__'] = slots.keys()
        return type.__new__(cls, name, bases, dct)


def InitAttrs(ob, args):
    for k, v in args.iteritems():
        if k[:1] == '_':
            setattr(ob, k[1:], v)

'''
If you would like to automatically assign arguments to methods
to the attributes of an object, you can do so by prefixing those
local variable names with a a single leading underscore '_',
which will be stripped from the instance variable (_x becomes x).


class Foo(object):
    def __init__(self, _x, _y, _z):
        InitAttrs(self, locals())
        #...


AutoSlots further allows you to automatically generate __slots__
for your classes, pulling the variables which need to be slots
from the arguments to the __init__ method on your class.

class Goo(object):
    __metaclass__ = AutoSlots
    def __init__(self, _x, _y, _z):
        InitAttrs(self, locals())
        #...


>>> x = Goo(1,2,3)
>>> [i for i in dir(x) if i[:1] != '_']
['x', 'y', 'z']
>>> x.a = 7
Traceback (most recent call last):
  File "<stdin>", line 1, in ?
AttributeError: 'Goo' object has no attribute 'a'
>>>

'''
