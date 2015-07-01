# -*- coding:utf-8 -*-
'''
This recipe creates a metaclass, that can be used in any dict-like object to map specially named attributes to keys of that dictionary.

By default, such attributes are those whose name begin with one (and only one) underscore, and they are mapped to the dictionary key of the same name, without the underscore; but the method to determine that behavior is overridable.

For instance, accessing: d._somekey would return: d.["somekey"]

Creation, update and deletion of such attributes works as expected.

While this class was designed to make a set of dict-like configuration classes more convenient to use, it is also primarily an exercise of style. Accessing conf._somekey is a tiny little bit more convenient and readable than conf["somekey"], or at least sufficiently so as to make the exercise of cleanly encapsulating syntactical magic into a metaclass worth attempting.

This recipe can obviously not access keys that are not valid attribute names. For instance, there will be no way to access d["a.b"] as an attribute. Interestingly, the native setattr() function suffers the same shortcoming: setattr(someobject, "a.b", "some value") will work, but there will be no way to access that attribute directly. This is one case where the Python abstraction of storing an object's attributes in its __dict__ dictionary shows through the seams.

'''
# ---[ Exception NotSpecialAttributeName ]----------------------------


class NotSpecialAttributeName(AttributeError):

    """
    NotSpecialAttributeName(AttributeError)

    Internal use only.
    This exception is used to distinguish between 'normal' attributes
    and the ones, identified by having one '_' as their first character,
    that are to be magically mapped to dictionary keys by the
    MetaDictProxy metaclass.
    """
    pass


# ---[ Class MetaDictProxy ]------------------------------------------

class MetaDictProxy(type):

    """
    MetaDictProxy(type)

    Metaclass that makes the items of a dictionary-like class accessible
    as attributes. Set it as a the metaclass for that class, and you can
    then access:
      d["somekey"]
    as:
      d._somekey
    It requires the target class to have the __{set|get|del}item__ methods
    of a dictionary.
    """

    def __init__(cls, name, bases, dict):

        super(MetaDictProxy, cls).__init__(name, bases, dict)
        setattr(cls, '__setattr__', MetaDictProxy.__mysetattr)
        setattr(cls, '__getattr__', MetaDictProxy.__mygetattr)
        setattr(cls, '__delattr__', MetaDictProxy.__mydelattr)

    @staticmethod
    def validatedAttr(attr):
        """
        validatedAttr(attr)

        Static method. Determines whether the parameter begins with one
        underscore '_' but not two. Raises NotSpecialAttributeName otherwise.
        Attributes beginning with one underscore will be looked up in the
        mapped dictionary.
        """

        if len(attr) > 2 \
                and attr.startswith("_") \
                and not attr.startswith("__"):

            return attr[1:]

        raise NotSpecialAttributeName(attr)

    @staticmethod
    def __mygetattr(obj, attr):

        try:
            vattr = MetaDictProxy.validatedAttr(attr)

        except NotSpecialAttributeName:
            # This is neither an existing native attribute, nor a 'special'
            # attribute name that should be read off the mapped dictionary,
            # so we raise an AttributeError.
            raise AttributeError(attr)

        try:
            return obj[vattr]

        except KeyError:
            raise AttributeError(attr)

    @staticmethod
    def __mysetattr(obj, attr, value):

        try:
            attr = MetaDictProxy.validatedAttr(attr)

        except NotSpecialAttributeName:
            # If this is a 'normal' attribute, treat it the normal way
            # and then return.
            obj.__dict__[attr] = value
            return

        obj[attr] = value

    @staticmethod
    def __mydelattr(obj, attr):

        try:
            vattr = MetaDictProxy.validatedAttr(attr)

        except NotSpecialAttributeName:
            # If this is a 'normal' attribute, treat it the normal way
            # and then return.
            try:
                del obj.__dict__[attr]

            except KeyError:
                raise AttributeError(attr)

            return

        try:
            del obj[vattr]

        except KeyError:
            raise AttributeError(attr)


# ---[ Example ]------------------------------------------------------

if __name__ == '__main__':

    class MyDict(dict):
        # We're wrapping dict here, but it would work with any dict-like
        # object.
        __metaclass__ = MetaDictProxy

    d = MyDict()

    d["foo"] = "bar"
    assert d._foo == "bar"
    del d._foo
    assert "foo" not in d.keys()

    # Non-special attributes aren't affected by this behavior:
    d.baz = "bux"
    d.__baz = "bux too"
    assert "baz" not in d.keys()
    assert "_baz" not in d.keys()
    assert "__baz" not in d.keys()
