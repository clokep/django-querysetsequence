import unittest

from django.test import TestCase

# In-case someone doesn't have Django REST Framework installed, guard tests.
try:
    from rest_framework import exceptions, filters
    from rest_framework.request import Request
    from rest_framework.test import APIRequestFactory

    factory = APIRequestFactory()

    from queryset_sequence.pagination import SequenceCursorPagination
except ImportError:
    factory = None

from queryset_sequence import QuerySetSequence

from tests.models import Author, Book, Publisher


@unittest.skipIf(not factory, 'Must have Django REST Framework installed to run pagination tests.')
class TestSequenceCursorPagination(TestCase):
    """
    Unit tests for `queryset_sequence.pagination.SequenceCursorPagination`.

    Heavily based on `tests.test_pagination` from Django REST Framework.
    """

    PAGE_1 = [1, 2, 3, 4, 5]
    PAGE_2 = [6, 7, 8, 9, 10]
    PAGE_3 = [11, 12, 13, 14]

    def setUp(self):
        class ExamplePagination(SequenceCursorPagination):
            page_size = 5
            # The test models don't have a 'created' field.
            ordering = 'pages'

        author = Author.objects.create(name="Jane Doe")
        publisher = Publisher.objects.create(name="Pablo's Publishing",
                                             address="123 Publishing Street")

        for d in range(1, 15):
            book = Book.objects.create(title='Book %s' % d,
                                       author=author,
                                       publisher=publisher,
                                       pages=d)

        self.pagination = ExamplePagination()
        self.queryset = QuerySetSequence(Book.objects.filter(pages__lte=7),
                                         Book.objects.filter(pages__gt=7))

    def get_pages(self, url):
        """
        Given a URL return a tuple of:
        (previous page, current page, next page, previous url, next url)
        """
        request = Request(factory.get(url))
        queryset = self.pagination.paginate_queryset(self.queryset, request)
        current = [item.pages for item in queryset]

        next_url = self.pagination.get_next_link()
        previous_url = self.pagination.get_previous_link()

        if next_url is not None:
            request = Request(factory.get(next_url))
            queryset = self.pagination.paginate_queryset(self.queryset, request)
            next = [item.pages for item in queryset]
        else:
            next = None

        if previous_url is not None:
            request = Request(factory.get(previous_url))
            queryset = self.pagination.paginate_queryset(self.queryset, request)
            previous = [item.pages for item in queryset]
        else:
            previous = None

        return (previous, current, next, previous_url, next_url)

    def test_ordering(self):
        """Ensure that the QuerySetSequence is ordered as expected."""
        pages = [b.pages for b in self.queryset]
        self.assertEqual(pages, self.PAGE_1 + self.PAGE_2 + self.PAGE_3)

        # The first 7 are in the 0th list, the last 7 are in the 1st list.
        number = [getattr(b, '#') for b in self.queryset]
        self.assertEqual(number, [0] * 7 + [1] * 7)

    def test_invalid_cursor(self):
        request = Request(factory.get('/', {'cursor': '123'}))
        with self.assertRaises(exceptions.NotFound):
            self.pagination.paginate_queryset(self.queryset, request)

    def test_use_with_ordering_filter(self):
        class MockView:
            filter_backends = (filters.OrderingFilter,)
            ordering_fields = ['title', 'author']
            ordering = 'title'

        request = Request(factory.get('/', {'ordering': 'author'}))
        ordering = self.pagination.get_ordering(request, [], MockView())
        self.assertEqual(ordering, ('#', 'author',))

        request = Request(factory.get('/', {'ordering': '-author'}))
        ordering = self.pagination.get_ordering(request, [], MockView())
        self.assertEqual(ordering, ('#', '-author',))

        request = Request(factory.get('/', {'ordering': 'invalid'}))
        ordering = self.pagination.get_ordering(request, [], MockView())
        self.assertEqual(ordering, ('#', 'title',))

    def test_cursor_pagination(self):
        (previous, current, next, previous_url, next_url) = self.get_pages('/')

        self.assertIsNone(previous)
        self.assertEqual(current, self.PAGE_1)
        self.assertEqual(next, self.PAGE_2)

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        self.assertEqual(previous, self.PAGE_1)
        self.assertEqual(current, self.PAGE_2)
        self.assertEqual(next, self.PAGE_3)

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        self.assertEqual(previous, self.PAGE_2)
        self.assertEqual(current, self.PAGE_3)
        self.assertIsNone(next)
