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
