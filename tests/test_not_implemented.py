from django.test import TestCase
from django.utils import six

from queryset_sequence import QuerySetSequence

from tests.models import Article


class MetaTestGenerator(type):
    """Generate identical test method off of a list of data."""

    ATTRIBUTES = []
    EXPECTED_EXCEPTION = RuntimeError

    def __new__(meta, name, bases, dct):
        # Give the test function a separate namespace.
        def gen_test_func(attr):
            def test(self):
                with self.assertRaises(meta.EXPECTED_EXCEPTION):
                    getattr(self.qss, attr)()
            test.__doc__ = ("Ensure that NotImplementedError is raised when "
                            "accessing '%s'" % attr)
            return test

        for attr in meta.ATTRIBUTES:
            dct['test_' + attr] = gen_test_func(attr)

        return type.__new__(meta, name, bases, dct)


class NotImplementedMeta(MetaTestGenerator):
    ATTRIBUTES = [
        # Methods that return QuerySets.
        'annotate',
        'distinct',
        'values',
        'values_list',
        'dates',
        'datetimes',
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
        'update',
    ]
    EXPECTED_EXCEPTION = NotImplementedError


class TestNotImplemented(six.with_metaclass(NotImplementedMeta, TestCase)):
    """Test methods that are not implemented and should raise NotImplemented."""

    @classmethod
    def setUpClass(cls):
        """Set-up some data to be tested against."""
        cls.qss = QuerySetSequence(Article.objects.all())

    @classmethod
    def tearDownClass(cls):
        del cls.qss


class AttributeErrorMeta(MetaTestGenerator):
    ATTRIBUTES = [
        # Private methods used by not implemented methods.
        '_populate_pk_values',
        '_create_object_from_params',
        '_extract_model_params',
        '_earliest_or_latest',
        '_raw_delete',
        '_update',
        '_prefetch_related_objects',

        # Private methods.
        '_insert',
        '_batched_insert',
        '_next_is_sticky',
        '_merge_known_related_objects',
        '_setup_aggregate_query',
        '_as_sql',
        '_add_hints',
        '_has_filters',
        'is_compatible_query_object_type',
    ]
    EXPECTED_EXCEPTION = AttributeError


class TestAttributeError(six.with_metaclass(AttributeErrorMeta, TestCase)):
    """Test methods that are not implemented and should raise NotImplemented."""

    @classmethod
    def setUpClass(cls):
        """Set-up some data to be tested against."""
        cls.qss = QuerySetSequence(Article.objects.all())

    @classmethod
    def tearDownClass(cls):
        del cls.qss
