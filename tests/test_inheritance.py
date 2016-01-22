from unittest import TestCase

from queryset_sequence import PartialInheritanceMeta


class A(object):
    a = 1
    b = True
    c = 72

    def __init__(self):
        self.z = 42


class B(A):
    __metaclass__ = PartialInheritanceMeta
    INHERITED_ATTRS = ['a']
    NOT_IMPLEMENTED_ATTRS = ['b']

    def __init__(self):
        self.y = 24


class TestPartialInheritanceMeta(TestCase):
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
        with self.assertRaises(AttributeError):
            self.b.z

    def test_dynamic(self):
        """Test an attribute in an object's __dict__."""
        self.assertTrue(hasattr(self.b, 'y'))
        self.assertEqual(self.b.y, 24)

    def test_not_implemented(self):
        self.assertTrue(hasattr(self.a, 'b'))
        self.assertEqual(self.a.b, True)

        self.assertTrue(hasattr(self.b, 'b'))
        self.assertRaises(NotImplementedError, self.b.b)

    def test_attr_error(self):
        self.assertTrue(hasattr(self.a, 'c'))
        self.assertEqual(self.a.c, 72)

        self.assertFalse(hasattr(self.b, 'c'))
        with self.assertRaises(AttributeError):
            self.b.c

    def test_attr_error2(self):
        self.assertFalse(hasattr(self.a, 'm'))
        with self.assertRaises(AttributeError):
            self.a.m

        self.assertFalse(hasattr(self.b, 'm'))
        with self.assertRaises(AttributeError):
            self.b.m
