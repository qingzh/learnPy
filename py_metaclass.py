import time
import sys


class MyMeta(type):

    @staticmethod
    def time_method(method):
        def __wrapper(self, *args, **kwargs):
            start = time.time()
            result = method(self, *args, **kwargs)
            finish = time.time()
            sys.stdout.write('instancemethod %s took %0.3f s.\n' % (
                method.__name__, (finish - start)))
            return result
        return __wrapper

    def __new__(cls, name, bases, attrs):
        print 'MyMeta __new__', name
        for attr in attrs:
            if attr in ['__init__', 'run']:
                continue
            attrs[attr] = cls.time_method(attrs[attr])
        return super(MyMeta, cls).__new__(cls, name, bases, attrs)

    def __init__(cls, *args, **kwargs):
        print 'Mymeta __init__', cls


class MyClass0(object):
    __metaclass__ = MyMeta

    # def __init__(self): pass

    def run(self):
        sys.stdout.write('running...')
        return True


class MyClass1(MyClass0):

    def run0(self):
        for i in xrange(1 << 15):
            a = i / 0.79
    ''' I need the inherited 'run' to be timed. '''
