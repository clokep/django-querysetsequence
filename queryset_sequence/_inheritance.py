import functools


class PartialInheritanceError(Exception):
    """An object is incorrectly configured when using PartialInheritanceMeta."""


class PartialInheritanceMeta(type):
    """
    A metaclass which allows partial inheritance of attributes from a
    superclass. Generally this is a bad design decision, unless you don't
    control the superclass and want to keep most of the code of a subclass in
    sync.

    In particular this metaclass:
        * Raises NotImplementedError for all attributes provided in
          NOT_IMPLEMENTED_ATTRS.
        * Allows access (i.e. inheritance) for all attributes provided in
          INHERITED_ATTRS.
        * Allows access (i.e. inheritance) for all magic methods.
        * Allows access for all attributes defined on the subclass or subclass
          instance.
        * Otherwise, raises AttributeError.

    """
    def __new__(meta, name, bases, dct):
        # Pull out special properties first.
        try:
            INHERITED_ATTRS = dct['INHERITED_ATTRS']
            del dct['INHERITED_ATTRS']
        except KeyError:
            raise PartialInheritanceError(
                "Class '%s' must provide 'INHERITED_ATTRS'." % name)

        try:
            NOT_IMPLEMENTED_ATTRS = dct['NOT_IMPLEMENTED_ATTRS']
            del dct['NOT_IMPLEMENTED_ATTRS']

            # For each not implemented attribute, add a method raising
            # NotImplementedError.
            def not_impl(attr):
                raise NotImplementedError("%s does not implement %s()" %
                                          (name, attr))

            for attr in NOT_IMPLEMENTED_ATTRS:
                dct[attr] = functools.partial(not_impl, attr)
        except KeyError:
            raise PartialInheritanceError(
                "Class '%s' must provide 'NOT_IMPLEMENTED_ATTRS'." % name)

        # Create the actual class.
        cls = type.__new__(meta, name, bases, dct)

        # Monkey-patch the class to modify how attributes are gotten.
        def __getattribute__(self, attr):
            # If the attribute is part of the following, just use a standard
            # __getattribute__:
            #   This class' attributes
            #   This instance's attributes
            #   A specifically inherited attribute
            #   A magic method
            __dict__ = super(cls, self).__getattribute__('__dict__')
            if (attr in dct or  # class attribute
                    attr in INHERITED_ATTRS or  # inherited attribute
                    attr in __dict__ or  # instance attribute
                    (attr.startswith('__') and attr.endswith('__'))):  # magic method
                return super(cls, self).__getattribute__(attr)

            # Finally, pretend the attribute doesn't exist.
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (name, attr))
        cls.__getattribute__ = __getattribute__

        return cls
