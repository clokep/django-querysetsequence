from django.test import TestCase

from queryset_sequence import QuerySetSequence

from .models import Article


class MetaTestGenerator(type):
    """Generate identical test method off of a list of data."""

    NOT_IMPLEMENTED = [
        # Methods that return QuerySets.
        'annotate',
        'reverse',
        'distinct',
        'values',
        'values_list',
        'dates',
        'datetimes',
        'none',
        'select_related',
        'prefetch_related',
        'extra',
        'defer',
        'only',
        'using',
        'select_for_update',
        'raw',

        # Methods that don't return QuerySets.
        'create',
        'get_or_create',
        'update_or_create',
        'bulk_create',
        'in_bulk',
        'latest',
        'earliest',
        'first',
        'last',
        'aggregate',
        'exists',
        'update',
        'delete',
    ]

    def __new__(meta, name, bases, dct):
        # Give the test function a separate namespace.
        def gen_test_func(attr):
            def test(self):
                self.assertRaises(NotImplementedError, getattr(self.qss, attr))
            test.__doc__ = ("Ensure that NotImplementedError is raised when "
                            "accessing '%s'" % attr)
            return test

        for attr in meta.NOT_IMPLEMENTED:
            dct['test_' + attr] = gen_test_func(attr)

        return type.__new__(meta, name, bases, dct)


class TestNotImplemented(TestCase):
    """Test methods that are not implemented and should raise NotImplemented."""
    __metaclass__ = MetaTestGenerator

    @classmethod
    def setUpClass(cls):
        """Set-up some data to be tested against."""
        cls.qss = QuerySetSequence(Article.objects.all())

    @classmethod
    def tearDownClass(cls):
        del cls.qss
