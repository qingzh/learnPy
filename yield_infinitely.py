def gg(n=2):
    for i in xrange(n):
        yield i


def ggg():  # infinitely
    g = gg()
    while True:
        try:
            flag = yield g.next()
            if flag is False:
                raise StopIteration
        except StopIteration:
            if flag is not False:
                g = gg()
            else:
                raise
