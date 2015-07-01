
Some thing about type(), isinstance()

class Foo(object):

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False


class Bar(Foo):pass


class Cow(Bar): pass

# Situation 1:
  compare two object:

>>> b = Bar()
>>> f = Foo()
>>> b == f
False
>>> f == b
True

>>> isinstance(b, Foo)
True
>>> isinstance(f, Bar)
False

## New Style Class
>>> type(b) == type(f)
False
>>> type(b) is type(f)
False
>>> type(f) == Foo
True
>>> type(f) == Bar
False
>>> type(f.__class__)
type

## Old Style Class
class Foo: pass
class Bar(Foo): pass

>>> type(b) == type(f)
True
>>> type(f) == type(b)
True

>>> f.__class__
<class __main__.Foo at 0x6fffa68df58>

>>> Foo
<class __main__.Foo at 0x6fffa68df58>

>>> type(f) == Foo
False

>>> type(f) == Bar
False

>>> f.__class__
<class __main__.Foo at 0x6fffa68df58>

>>> type(f.__class__)
classobj

>>> type(f) == Bar
False

>>> type(b) == Foo
False

>>> type(b) == Bar
False

>>> type(f) == type(b)
True

>>> b.__class__
<class __main__.Bar at 0x6fffab75738>

>>> f.__class__
<class __main__.Foo at 0x6fffa68df58>

>>> c = Cow()
>>> type(c) is Bar
False
>>> type(c) == Bar
False
>>> Bar is type(c)
False
>>> Bar == type(c)
False
>>> isinstance(c, Bar)
True

# New Style Class