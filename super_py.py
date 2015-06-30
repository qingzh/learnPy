class Base(object):

    def __init__(self):
        print "Base created"


class ChildA(Base):

    def __init__(self):
        print 'ChildA'
        Base.__init__(self)


class ChildB(Base):

    def __init__(self):
        print 'ChildB'
        super(ChildB, self).__init__()

'''
Super has no side effects
'''
# works as expected
Base = ChildB
base()

# gets into infinite recursion
Base = ChildA
Base()
