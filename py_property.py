class Test(object):
    PROFILE = None

    @property
    def profile(self):
        print 'get profile of %s' % self
        return self.PROFILE
    @profile.setter
    def profile(self, value):
        print 'set profile of %s' % self
        if isinstance(value, int):
            self.PROFILE = 'int: %s'% value
        else:
            self.PROFILE = value

    def try_profile(self, value):
        print 'try profile of %s' % self
        # Do NOT use self.profile(value)
        a.__class__.__dict__['profile'].__set__(self, value)

        