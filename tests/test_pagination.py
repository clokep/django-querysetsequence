from datetime import date
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
    SequenceCursorPagination = object

from queryset_sequence import QuerySetSequence

from tests.models import Author, Book, Publisher


class _TestPagination(SequenceCursorPagination):
    """A SequenceCursorPagination with a small page_size."""
    page_size = 5
    # The test models don't have a 'created' field.
    ordering = 'pages'


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
        self.author = Author.objects.create(name="Jane Doe")
        self.publisher = Publisher.objects.create(name="Pablo's Publishing",
                                                  address="123 Publishing Street")

        for d in range(1, 15):
            Book.objects.create(title='Book %s' % (d % 2),
                                author=self.author,
                                publisher=self.publisher,
                                pages=d,
                                release=date(2018, 10, 5))

        self.pagination = _TestPagination()
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
        """Ensure that the cursor properly flips through pages."""
        # Check the first page.
        (previous, current, next, previous_url, next_url) = self.get_pages('/')

        self.assertIsNone(previous)
        self.assertEqual(current, self.PAGE_1)
        self.assertEqual(next, self.PAGE_2)

        # Check the second page.
        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        self.assertEqual(previous, self.PAGE_1)
        self.assertEqual(current, self.PAGE_2)
        self.assertEqual(next, self.PAGE_3)

        # Check the third page.
        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        self.assertEqual(previous, self.PAGE_2)
        self.assertEqual(current, self.PAGE_3)
        self.assertIsNone(next)

    def test_cursor_stableness(self):
        """
        Test what happens if we remove domains after loading a page.
        Pages should be independent, i.e. a cursor points to a particular
        domain, and shouldn't affect offsets.
        """
        (previous, current, next, previous_url, next_url) = self.get_pages('/')

        # The first page is as normal.
        self.assertIsNone(previous)
        self.assertEqual(current, self.PAGE_1)
        self.assertEqual(next, self.PAGE_2)

        # Delete Books, this shouldn't affect the next request.
        Book.objects.filter(pages__lte=3).delete()
        Book.objects.filter(pages__gte=13).delete()

        (previous, current, next, _, old_next_url) = self.get_pages(next_url)

        # Should be some missing items
        self.assertEqual(previous, [4, 5])
        self.assertEqual(current, self.PAGE_2)
        self.assertEqual(next, [11, 12])

        # Deleting some from the current page and reloading should have the page
        # offset.
        Book.objects.get(pages=7).delete()

        (previous, current, next, _, new_next_url) = self.get_pages(next_url)

        # Should be some missing items
        self.assertEqual(previous, [4, 5])
        self.assertEqual(current, [6, 8, 9, 10, 11])
        self.assertEqual(next, [12])

        # The next_url returned with the different items missing will actually
        # be different.
        self.assertNotEqual(old_next_url, new_next_url)

    def test_multiple_ordering(self):
        """Test a Pagination with multiple items in the ordering attribute."""

        # This will order by:
        #   1. Even pages
        #   2. Odd pages
        #   3. Both of the above will be done in increasing order.
        #   4. Ordering happens for 1 - 7, then 8 - 14.
        class TestPagination(_TestPagination):
            ordering = ['title', 'pages']

        self.pagination = TestPagination()

        PAGE_1 = [2, 4, 6, 1, 3]
        PAGE_2 = [5, 7, 8, 10, 12]
        PAGE_3 = [14, 9, 11, 13]

        # Check that the ordering is as expected.
        pages = [b.pages for b in self.queryset.order_by('#', *self.pagination.ordering)]
        self.assertEqual(pages, PAGE_1 + PAGE_2 + PAGE_3)

        # Now perform pretty much the same test as test_cursor_pagination, but
        # the ordering will be different.
        (previous, current, next, previous_url, next_url) = self.get_pages('/')

        self.assertIsNone(previous)
        self.assertEqual(current, PAGE_1)
        self.assertEqual(next, PAGE_2)

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        self.assertEqual(previous, PAGE_1)
        self.assertEqual(current, PAGE_2)
        self.assertEqual(next, PAGE_3)

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        self.assertEqual(previous, PAGE_2)
        self.assertEqual(current, PAGE_3)
        self.assertIsNone(next)

    def test_duplicates(self):
        """Ensure that pagination works over an 'extreme' number of duplicates."""
        PAGES = 100 # This must be unique from other fixture data.

        # Create a bunch of books that are the same.
        for i in range(15):
            Book.objects.create(title=str(i),
                                author=self.author,
                                publisher=self.publisher,
                                pages=PAGES,
                                release=date(2018, 10, 5))

        # And use only those duplicate books.
        self.queryset = QuerySetSequence(Book.objects.filter(pages=PAGES))

        titles = [item.title for item in self.queryset]

        # Look at both the pages (which should all be 1) and the IDs.
        next_url = '/'
        for i in range(3):
            request = Request(factory.get(next_url))
            queryset = self.pagination.paginate_queryset(self.queryset, request)
            titles, pages = zip(*[(item.title, item.pages) for item in queryset])

            self.assertEqual(titles, tuple(map(lambda d: str(d + (i * 5)), [0, 1, 2, 3, 4])))
            self.assertEqual(pages, (PAGES, ) * 5)

            next_url = self.pagination.get_next_link()

        self.assertIsNone(next_url)
