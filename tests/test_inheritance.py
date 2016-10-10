from unittest import TestCase

from django.utils import six

from queryset_sequence._inheritance import (PartialInheritanceError,
                                            PartialInheritanceMeta)


class A(object):
    a = 1
    b = True
    c = 72
    d = 90

    def e(self):
        return 17

    def __init__(self):
        self.z = 42

    def __str__(self):
        return ('%s(a = %s)' % (self.__class__.__name__, self.a))


class B(six.with_metaclass(PartialInheritanceMeta, A)):
    INHERITED_ATTRS = ['a', 'e']
    NOT_IMPLEMENTED_ATTRS = ['b', 'd']

    f = True

    def __init__(self):
        self.y = 24

    def e(self):
        result = super(B, self).e()
        return -result


class TestPartialInheritanceMeta(TestCase):
    def assertExceptionMessageEquals(self, exception, expected):
        result = exception.message if six.PY2 else exception.args[0]
        self.assertEqual(expected, result)

    def setUp(self):
        self.a = A()
        self.b = B()

    def test_inherited(self):
        self.assertTrue(hasattr(self.a, 'a'))
        self.assertEqual(self.a.a, 1)

        self.assertTrue(hasattr(self.b, 'a'))
        self.assertEqual(self.b.a, 1)

    def test_inherited_dynamic(self):
        """Test an attribute inherited into __dict__."""
        self.assertTrue(hasattr(self.a, 'z'))
        self.assertEqual(self.a.z, 42)

        self.assertFalse(hasattr(self.b, 'z'))
        with self.assertRaises(AttributeError) as exc:
            self.b.z
        self.assertExceptionMessageEquals(exc.exception,
                                          "'B' object has no attribute 'z'")

    def test_dynamic(self):
        """Test an attribute in an object's __dict__."""
        self.assertTrue(hasattr(self.b, 'y'))
        self.assertEqual(self.b.y, 24)

    def test_not_implemented(self):
        self.assertTrue(hasattr(self.a, 'b'))
        self.assertEqual(self.a.b, True)

        self.assertTrue(hasattr(self.b, 'b'))
        with self.assertRaises(NotImplementedError) as exc:
            self.b.b()
        self.assertExceptionMessageEquals(exc.exception,
                                          'B does not implement b()')

    def test_attr_error(self):
        self.assertTrue(hasattr(self.a, 'c'))
        self.assertEqual(self.a.c, 72)

        self.assertFalse(hasattr(self.b, 'c'))
        with self.assertRaises(AttributeError) as exc:
            self.b.c
        self.assertExceptionMessageEquals(exc.exception,
                                          "'B' object has no attribute 'c'")

    def test_attr_error2(self):
        self.assertFalse(hasattr(self.a, 'm'))
        with self.assertRaises(AttributeError) as exc:
            self.a.m
        self.assertExceptionMessageEquals(exc.exception,
                                          "'A' object has no attribute 'm'")

        self.assertFalse(hasattr(self.b, 'm'))
        with self.assertRaises(AttributeError) as exc:
            self.b.m
        self.assertExceptionMessageEquals(exc.exception,
                                          "'B' object has no attribute 'm'")

    def test_subclass_attr(self):
        self.assertFalse(hasattr(self.a, 'f'))
        with self.assertRaises(AttributeError) as exc:
            self.a.f
        self.assertExceptionMessageEquals(exc.exception,
                                          "'A' object has no attribute 'f'")

        self.assertTrue(hasattr(self.b, 'f'))
        self.assertEqual(self.b.f, True)

    def test_magic_method(self):
        self.assertTrue(hasattr(self.a, '__str__'))
        self.assertEqual(self.a.__str__(), 'A(a = 1)')

        self.assertTrue(hasattr(self.b, '__str__'))
        self.assertEqual(self.b.__str__(), 'B(a = 1)')

    def test_super(self):
        self.assertTrue(hasattr(self.a, 'e'))
        self.assertEqual(self.a.e(), 17)

        self.assertTrue(hasattr(self.b, 'e'))
        self.assertEqual(self.b.e(), -17)

    def test_undefined_inherited_attrs(self):
        """Test for when a sub-class doesn't define INHERITED_ATTRS."""
        with self.assertRaises(PartialInheritanceError) as exc:
            class C(six.with_metaclass(PartialInheritanceMeta, A)):
                """A class that doesn't define INHERITED_ATTRS."""

        self.assertExceptionMessageEquals(exc.exception,
                                          "Class 'C' must provide 'INHERITED_ATTRS'.")

    def test_undefined_not_implemented_attrs(self):
        """Test for when a sub-class doesn't define NOT_IMPLEMENTED_ATTRS."""
        with self.assertRaises(PartialInheritanceError) as exc:
            class D(six.with_metaclass(PartialInheritanceMeta, A)):
                """A class that doesn't define NOT_IMPLEMENTED_ATTRS."""
                INHERITED_ATTRS = []

        self.assertExceptionMessageEquals(exc.exception,
                                          "Class 'D' must provide 'NOT_IMPLEMENTED_ATTRS'.")
