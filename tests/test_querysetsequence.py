from __future__ import unicode_literals

from datetime import date
from unittest import skip, skipIf

import django
from django.core.exceptions import (FieldDoesNotExist,
                                    FieldError,
                                    MultipleObjectsReturned,
                                    ObjectDoesNotExist)
from django.db.models import Count
from django.db.models.query import EmptyQuerySet
from django.test import TestCase

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from queryset_sequence import QuerySetSequence

from tests.models import (Article, Author, BlogPost, Book, OnlinePublisher,
                          PeriodicalPublisher, Publisher)


class TestBase(TestCase):
    # The title of each Book, followed by each Article; each ordered by primary
    # key. This matches all without any transforms applied.
    TITLES_BY_PK = [
        'Fiction',
        'Biography',
        'Django Rocks',
        'Alice in Django-land',
        'Some Article',
    ]

    def setUp(self):
        """Set-up some data to be tested against."""
        alice = Author.objects.create(name="Alice")
        bob = Author.objects.create(name="Bob")

        # Purposefully ordered such that the pks will be in the opposite order
        # than the names.
        mad_magazine = PeriodicalPublisher.objects.create(name="Mad Magazine")
        # This publisher is unused, just takes up a PK in the database.
        Publisher.objects.create(name="Unused Publisher")
        big_books = Publisher.objects.create(name="Big Books",
                                             address="123 Street")
        wacky_website = OnlinePublisher.objects.create(name="Wacky Website")

        # Alice wrote some articles.
        Article.objects.create(title="Django Rocks", author=alice,
                               publisher=mad_magazine, release=date(1980, 4, 21))
        Article.objects.create(title="Alice in Django-land", author=alice,
                               publisher=mad_magazine, release=date(1990, 8, 14))

        # Bob wrote a couple of books, an article, and a blog post.
        Book.objects.create(title="Fiction", author=bob, publisher=big_books,
                            pages=10, release=date(2001, 6, 12))
        Book.objects.create(title="Biography", author=bob, publisher=big_books,
                            pages=20, release=date(2002, 12, 24))
        Article.objects.create(title="Some Article", author=bob,
                               publisher=mad_magazine, release=date(1979, 1, 1))
        BlogPost.objects.create(title="Post", author=bob,
                                publisher=wacky_website)

        # Save the authors and publishers for later.
        self.alice = alice
        self.bob = bob
        self.big_books = big_books
        self.mad_magazine = mad_magazine
        self.wacky_website = wacky_website

        # Many tests start with the same QuerySetSequence.
        self.all = QuerySetSequence(Book.objects.all(), Article.objects.all())

        # An empty QuerySetSequence.
        self.empty = QuerySetSequence()


class TestLength(TestBase):
    """
    Ensure that count() and len() are properly summed over the children
    QuerySets.
    """

    def test_count(self):
        # The proper length should be returned via database queries.
        with self.assertNumQueries(2):
            self.assertEqual(self.all.count(), 5)

        # Asking for it again should re-evaluate the query.
        with self.assertNumQueries(2):
            self.assertEqual(self.all.count(), 5)

    def test_len(self):
        # Calling len() evaluates the QuerySet.
        with self.assertNumQueries(2):
            self.assertEqual(len(self.all), 5)

        # Requesting this again should not cause any queries to occur.
        with self.assertNumQueries(0):
            self.assertEqual(len(self.all), 5)

    def test_slice(self):
        """Ensure the proper length is calculated when a slice is taken."""
        with self.assertNumQueries(2):
            self.assertEqual(self.all[1:].count(), 4)

        # This evaluates the QuerySets, which also causes count() on each to be
        # called.
        with self.assertNumQueries(4):
            self.assertEqual(len(self.all[1:]), 4)

    def test_empty_count(self):
        """An empty QuerySetSequence has a count of 0."""
        self.assertEqual(self.empty.count(), 0)

    def test_empty_len(self):
        """An empty QuerySetSequence has a count of 0."""
        self.assertEqual(len(self.empty), 0)


class TestIterator(TestBase):
    """Test the iterator when no ordering is set."""
    def test_iterator(self):
        """Ensure that an iterator queries for the results."""
        # Ensure that calling iterator twice re-evaluates the query.
        with self.assertNumQueries(2):
            data = [it.title for it in self.all.iterator()]
        self.assertEqual(data, TestIterator.TITLES_BY_PK)

        with self.assertNumQueries(2):
            data = [it.title for it in self.all.iterator()]
        self.assertEqual(data, TestIterator.TITLES_BY_PK)

    def test_iter(self):
        """Directly iteratoring the query should return the same results."""
        with self.assertNumQueries(2):
            data = [it.title for it in self.all]
        self.assertEqual(data, TestIterator.TITLES_BY_PK)

    def test_iter_cache(self):
        """Ensure that iterating the QuerySet caches."""
        with self.assertNumQueries(2):
            data = [it.title for it in self.all]
            self.assertEqual(data, TestIterator.TITLES_BY_PK)

        # So the second call does nothing.
        with self.assertNumQueries(0):
            data = [it.title for it in self.all]
            self.assertEqual(data, TestIterator.TITLES_BY_PK)

    def test_empty(self):
        """Test an empty iteration."""
        with self.assertNumQueries(0):
            self.assertEqual(list(self.empty.iterator()), [])

    def test_empty_iter(self):
        with self.assertNumQueries(0):
            self.assertEqual(list(self.empty), [])

    def test_empty_subqueryset(self):
        """Iterating an empty set should work."""
        qss = QuerySetSequence(Book.objects.all(), Article.objects.none()).order_by('title')

        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        self.assertEqual(data, ['Biography', 'Fiction'])


class TestOperators(TestBase):
    def test_and_identity(self):
        """ANDing with an EmptyQuerySet returns an EmptyQuerySet."""
        with self.assertNumQueries(0):
            combined = self.all & BlogPost.objects.none()
        self.assertIsInstance(combined, EmptyQuerySet)

    def test_and(self):
        """ANDing with a QuerySet applies the and to each QuerySet and removes ones of differing types."""
        # ANDing with a different type of QuerySet ends up with an EmptyQuerySet.
        with self.assertNumQueries(0):
            combined = self.all & BlogPost.objects.all()
        self.assertIsInstance(combined, EmptyQuerySet)

        # ANDing with a QuerySet of a type in the QuerySetSequence applies the
        # AND to that QuerySet.
        with self.assertNumQueries(0):
            combined = self.all & Book.objects.filter(pages__lt=15)
        self.assertIsInstance(combined, QuerySetSequence)
        self.assertEqual(len(combined._querysets), 1)
        with self.assertNumQueries(1):
            data = [it.title for it in combined.iterator()]
        self.assertEqual(data, ['Fiction'])

    def test_empty_and(self):
        """An empty QuerySetSequence can be ANDed with a QuerySet, but returns an EmptyQuerySet."""
        combined = self.empty & BlogPost.objects.all()
        self.assertIsInstance(combined, EmptyQuerySet)
        self.assertEqual(list(combined), [])

    def test_or_identity(self):
        """ORing with an empty QuerySet should just return the same QuerySetSequence."""
        with self.assertNumQueries(0):
            combined = self.all | BlogPost.objects.none()
        self.assertIsInstance(combined, QuerySetSequence)
        self.assertEqual(len(combined._querysets), 2)

        with self.assertNumQueries(2):
            data = [it.title for it in combined.iterator()]
        self.assertEqual(data, self.TITLES_BY_PK)

    def test_or(self):
        """ORing with a QuerySet should add it to the list of QuerySets."""
        with self.assertNumQueries(0):
            combined = self.all | BlogPost.objects.all()
        self.assertIsInstance(combined, QuerySetSequence)
        self.assertEqual(len(combined._querysets), 3)

        with self.assertNumQueries(3):
            data = [it.title for it in combined.iterator()]
        self.assertEqual(data, self.TITLES_BY_PK + ['Post'])

    def test_or_querysetsequence(self):
        """ORing with a QuerySetSequence should combine the lists of QuerySets."""
        with self.assertNumQueries(0):
            combined = self.all | QuerySetSequence(BlogPost.objects.all())
        self.assertIsInstance(combined, QuerySetSequence)
        self.assertEqual(len(combined._querysets), 3)

        with self.assertNumQueries(3):
            data = [it.title for it in combined.iterator()]
        self.assertEqual(data, self.TITLES_BY_PK + ['Post'])

    def test_empty_or(self):
        """An empty QuerySetSequence can be ORed with a QuerySet, but returns an EmptyQuerySet."""
        combined = self.empty | BlogPost.objects.all()
        self.assertIsInstance(combined, QuerySetSequence)
        self.assertEqual(len(combined._querysets), 1)

        with self.assertNumQueries(1):
            data = [it.title for it in combined.iterator()]
        self.assertEqual(data, ['Post'])

    def test_empty_or_querysetsequence(self):
        combined = self.empty | QuerySetSequence(BlogPost.objects.all())
        self.assertIsInstance(combined, QuerySetSequence)
        self.assertEqual(len(combined._querysets), 1)

        with self.assertNumQueries(1):
            data = [it.title for it in combined.iterator()]
        self.assertEqual(data, ['Post'])


class TestNone(TestBase):
    def test_none(self):
        """
        Ensure an instance of EmptyQuerySet is returned and has no results (and
        doesn't perform queries).
        """
        with self.assertNumQueries(0):
            qss = self.all.none()
            data = list(qss)

        # This returns an EmptyQuerySet.
        self.assertIsInstance(qss, EmptyQuerySet)

        # Should have no data.
        self.assertEqual(data, [])

    @skip('Currently not working.')
    def test_empty(self):
        qss = self.empty.none()

        # This returns an EmptyQuerySet.
        self.assertIsInstance(qss, EmptyQuerySet)


class TestAll(TestBase):
    def test_all(self):
        """Ensure a copy is made when calling all()."""
        copy = self.all.all()

        # Different QuerySetSequences, but the same content.
        self.assertNotEqual(self.all, copy)

        # Each QuerySet should be evaluated separately.
        with self.assertNumQueries(2):
            data = [it.title for it in self.all]
        self.assertEqual(data, self.TITLES_BY_PK)

        with self.assertNumQueries(2):
            data = [it.title for it in copy]
        self.assertEqual(data, self.TITLES_BY_PK)

    def test_empty(self):
        """Copying an empty QuerySetSequence works fine."""
        copy = self.empty.all()

        # Different QuerySetSequences, but the same content.
        self.assertNotEqual(self.all, copy)
        self.assertEqual(list(copy), [])


class TestRelated(TestBase):
    """Tests for select_related and prefetch_related."""
    # Bob, Bob, Alice, Alice, Bob.
    EXPECTED_ORDER = [2, 2, 1, 1, 2]

    def test_no_related(self):
        """Check the behavior to ensure that iterating causes additional queries."""
        with self.assertNumQueries(2):
            books = list(self.all)
        with self.assertNumQueries(5):
            authors = [b.author.id for b in books]
        self.assertEqual(authors, self.EXPECTED_ORDER)

    def test_select_related(self):
        """Select related removes subsequent queries to get ForeignKeys."""
        with self.assertNumQueries(2):
            books = list(self.all.select_related('author'))
        with self.assertNumQueries(0):
            authors = [b.author.id for b in books]
        self.assertEqual(authors, self.EXPECTED_ORDER)

    # TODO Add a test for select_related that follows multiple ForeignKeys.

    def test_clear_select_related(self):
        """Clearing select related causes all the database queries to occur again."""
        # Ensure there is a database query.
        with self.assertNumQueries(2):
            books = list(self.all.select_related('author').select_related(None))
        with self.assertNumQueries(5):
            authors = [b.author.id for b in books]
        self.assertEqual(authors, self.EXPECTED_ORDER)

    def test_empty_select_related(self):
        """Calling select_related on an empty QuerySetSequence doesn't error."""
        self.empty.select_related('author')

    def test_prefetch_related(self):
        """Now ensure one database query for all authors, per QuerySet."""
        with self.assertNumQueries(4):
            books = list(self.all.prefetch_related('author'))
        with self.assertNumQueries(0):
            authors = [b.author.id for b in books]
        self.assertEqual(authors, self.EXPECTED_ORDER)

    # TODO Add a test for prefetch_related that follows multiple ForeignKeys.

    def test_clear_prefetch_related(self):
        """Ensure the original behavior is restored if prefetch related is cleared."""
        with self.assertNumQueries(2):
            books = list(self.all.prefetch_related('author').prefetch_related(None))
        with self.assertNumQueries(5):
            authors = [b.author.id for b in books]
        self.assertEqual(authors, self.EXPECTED_ORDER)

    def test_empty_prefetch_related(self):
        """Calling prefetch_related on an empty QuerySetSequence doesn't error."""
        self.empty.prefetch_related('author')


class TestDeferOnly(TestBase):
    def test_defer(self):
        """A deferred field will be loaded on access."""
        with self.assertNumQueries(2):
            books = list(self.all.defer('title'))
        with self.assertNumQueries(5):
            titles = [b.title for b in books]
        self.assertEqual(titles, self.TITLES_BY_PK)

    def test_clear_defer(self):
        """Ensure the original behavior is restored if defer is cleared."""
        with self.assertNumQueries(2):
            books = list(self.all.defer('title').defer(None))
        with self.assertNumQueries(0):
            titles = [b.title for b in books]
        self.assertEqual(titles, self.TITLES_BY_PK)

    def test_empty_defer(self):
        """Calling defer on an empty QuerySetSequence doesn't error."""
        self.empty.defer('title')

    def test_only(self):
        """Only causes other fields to load on access (opposite of defer)."""
        with self.assertNumQueries(2):
            books = list(self.all.only('publisher'))
        with self.assertNumQueries(5):
            titles = [b.title for b in books]
        self.assertEqual(titles, self.TITLES_BY_PK)

    # Note that you cannot clear an only call, so None is not a valid value.

    def test_empty_only(self):
        """Calling only on an empty QuerySetSequence doesn't error."""
        self.empty.only('publisher')


class TestUsing(TestBase):
    def test_using(self):
        """Using should be passed through to each QuerySet."""
        with self.assertNumQueries(2):
            titles = [b.title for b in self.all.using('default')]
        self.assertEqual(titles, self.TITLES_BY_PK)


class TestFilter(TestBase):
    def test_filter(self):
        """
        Ensure that filter() properly filters the children QuerySets, note that
        no QuerySets are actually evaluated during this.
        """
        # Filter to just Bob's work.
        with self.assertNumQueries(0):
            bob_qss = self.all.filter(author=self.bob)
        with self.assertNumQueries(2):
            self.assertEqual(bob_qss.count(), 3)

    def test_filter_by_relation(self):
        """
        Ensure that filter() properly filters the children QuerySets when using
        a related model, note that no QuerySets are actually evaluated during
        this.
        """
        # Filter to just Bob's work.
        with self.assertNumQueries(0):
            bob_qss = self.all.filter(author__name=self.bob.name)
        with self.assertNumQueries(2):
            self.assertEqual(bob_qss.count(), 3)

    def test_empty(self):
        """
        Ensure that filter() works when it results in an empty QuerySet.
        """
        # Filter to nothing.
        with self.assertNumQueries(0):
            qss = self.all.filter(title='')
        self.assertIsInstance(qss, QuerySetSequence)
        with self.assertNumQueries(2):
            self.assertEqual(qss.count(), 0)

        # This should not throw an exception.
        data = list(qss)
        self.assertEqual(len(data), 0)

    def _get_qss(self):
        """Returns a QuerySetSequence with 3 QuerySets."""
        return QuerySetSequence(Book.objects.all(),
                                Article.objects.all(),
                                BlogPost.objects.all())

    def test_queryset(self):
        """Test filtering the QuerySets by exact lookups."""
        for key in ['#', '#__exact', '#__iexact']:
            with self.assertNumQueries(0):
                qss = self._get_qss().filter(**{key: 1})

            with self.assertNumQueries(1):
                data = [it.title for it in qss]
            expected = [
                # Just the Articles.
                'Django Rocks',
                'Alice in Django-land',
                'Some Article',
            ]
            self.assertEqual(data, expected)

    def test_queryset_gt(self):
        """Test filtering the QuerySets by > lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{'#__gt': 0})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            # The Articles and BlogPosts.
            'Django Rocks',
            'Alice in Django-land',
            'Some Article',
            'Post',
        ]
        self.assertEqual(data, expected)

        # Additionally this should cast a string input to an int.
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{'#__gt': '0'})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, expected)

    def test_queryset_gte(self):
        """Test filtering the QuerySets by >= lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{'#__gte': 1})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            # The Articles and BlogPosts.
            'Django Rocks',
            'Alice in Django-land',
            'Some Article',
            'Post',
        ]
        self.assertEqual(data, expected)

    def test_queryset_lt(self):
        """Test filtering the QuerySets by < lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{'#__lt': 2})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        # The Books and Articles are returned.
        self.assertEqual(data, self.TITLES_BY_PK)

    def test_queryset_lte(self):
        """Test filtering the QuerySets by <= lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{'#__lte': 1})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        # The Books and Articles.
        self.assertEqual(data, self.TITLES_BY_PK)

    def test_queryset_in(self):
        """Filter the QuerySets with the in lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{'#__in': [1]})

        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        expected = [
            # Just the Articles.
            'Django Rocks',
            'Alice in Django-land',
            'Some Article',
        ]
        self.assertEqual(data, expected)

    def test_queryset_str(self):
        """Try filtering the QuerySets by various string lookups."""
        for key in ['#__contains', '#__icontains', '#__startswith', '#__istartswith', '#__endswith', '#__iendswith']:
            with self.assertNumQueries(0):
                qss = self._get_qss().filter(**{key: 1})

            with self.assertNumQueries(1):
                data = [it.title for it in qss]
            expected = [
                # Just the Articles.
                'Django Rocks',
                'Alice in Django-land',
                'Some Article',
            ]
            self.assertEqual(data, expected)

    def test_queryset_range(self):
        """Try filtering the QuerySets by the range lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{'#__range': [1, 2]})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            # The Articles and BlogPosts.
            'Django Rocks',
            'Alice in Django-land',
            'Some Article',
            'Post',
        ]
        self.assertEqual(data, expected)

    def test_queryset_unsupported(self):
        """Try filtering the QuerySets by a lookup that doesn't make sense."""
        with self.assertRaises(ValueError):
            self._get_qss().filter(**{'#__year': 1})

    def test_queryset_multiple(self):
        """
        When using multiple paramters to filter they get ANDed together. Ensure
        this works when filtering by QuerySet.
        """
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{'#__gt': 0, 'title__gt': 'Django Rocks'})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            # Some of the Articles and the BlogPosts.
            'Some Article',
            'Post',
        ]
        self.assertEqual(data, expected)

        # This would only look at Articles and BlogPosts, but neither of those
        # have a title > "Some Article."
        qss = self._get_qss().filter(**{'#__gt': 0, 'title__gt': 'Some Article'})

        # Only the articles are here because it's the second queryset.
        data = [it.title for it in qss]
        self.assertEqual(data, [])

    def test_empty(self):
        """Calling filter on an empty QuerySetSequence doesn't error."""
        self.empty.filter(title='')


class TestExclude(TestBase):
    """
    Note that this is the same test as TestFilter, but we exclude the other
    author instead of filtering.
    """

    def test_exclude(self):
        """
        Ensure that exclude() properly filters the children QuerySets, note that
        no QuerySets are actually evaluated during this.
        """
        # Filter to just Bob's work.
        with self.assertNumQueries(0):
            bob_qss = self.all.exclude(author=self.alice)
        with self.assertNumQueries(2):
            self.assertEqual(bob_qss.count(), 3)

    def test_exclude_by_relation(self):
        """
        Ensure that exclude() properly filters the children QuerySets when using
        a related model, note that no QuerySets are actually evaluated during
        this.
        """
        # Filter to just Bob's work.
        with self.assertNumQueries(0):
            bob_qss = self.all.exclude(author__name=self.alice.name)
        with self.assertNumQueries(2):
            self.assertEqual(bob_qss.count(), 3)

    def test_empty(self):
        """
        Ensure that filter() works when it results in an empty QuerySet.
        """
        # Filter to nothing.
        with self.assertNumQueries(0):
            qss = self.all.exclude(author__in=[self.alice, self.bob])
        self.assertIsInstance(qss, QuerySetSequence)
        with self.assertNumQueries(2):
            self.assertEqual(qss.count(), 0)

        # This should not throw an exception.
        data = list(qss)
        self.assertEqual(len(data), 0)

    def _get_qss(self):
        """Returns a QuerySetSequence with 3 QuerySets."""
        return QuerySetSequence(Book.objects.all(),
                                Article.objects.all(),
                                BlogPost.objects.all())

    def test_queryset(self):
        """Test excluding the QuerySets by exact lookups."""
        for key in ['#', '#__exact', '#__iexact']:
            with self.assertNumQueries(0):
                qss = self._get_qss().exclude(**{key: 0})

            # The articles and blogposts are here because the first QuerySet is
            # removed.
            with self.assertNumQueries(2):
                data = [it.title for it in qss]
            expected = [
                # The Articles and BlogPosts.
                'Django Rocks',
                'Alice in Django-land',
                'Some Article',
                'Post',
            ]
            self.assertEqual(data, expected)

    def test_queryset_gt(self):
        """Test excluding the QuerySets by > lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{'#__gt': 1})

        # The books and articles are here.
        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        # The Books and Articles.
        self.assertEqual(data, self.TITLES_BY_PK)

    def test_queryset_gte(self):
        """Test excluding the QuerySets by >= lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{'#__gte': 1})

        # Only the blogposts are here because it's the last queryset.
        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        expected = [
            # Just the Books.
            'Fiction',
            'Biography',
        ]
        self.assertEqual(data, expected)

    def test_queryset_lt(self):
        """Test excluding the QuerySets by < lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{'#__lt': 1})

        # The articles and blogposts are here.
        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            # The Articles and BlogPosts.
            'Django Rocks',
            'Alice in Django-land',
            'Some Article',
            'Post',
        ]
        self.assertEqual(data, expected)

    def test_queryset_lte(self):
        """Test excluding the QuerySets by <= lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{'#__lte': 1})

        # Only the blogposts are here because it's the last queryset.
        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        expected = [
            # The BlogPosts.
            'Post',
        ]
        self.assertEqual(data, expected)

    def test_queryset_in(self):
        """exclude the QuerySets with the in lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{'#__in': [0, 2]})

        # Only the articles are here because it's the second queryset.
        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        expected = [
            # The Articles.
            'Django Rocks',
            'Alice in Django-land',
            'Some Article',
        ]
        self.assertEqual(data, expected)

    def test_queryset_str(self):
        """Try excluding the QuerySets by various string lookups."""
        for key in ['#__contains', '#__icontains', '#__startswith', '#__istartswith', '#__endswith', '#__iendswith']:
            with self.assertNumQueries(0):
                qss = self._get_qss().exclude(**{key: 1})

            # The books and blogposts are here.
            with self.assertNumQueries(2):
                data = [it.title for it in qss]
            expected = [
                # The Books and BlogPosts.
                'Fiction',
                'Biography',
                'Post',
            ]
            self.assertEqual(data, expected)

    def test_queryset_range(self):
        """Try excluding the QuerySets by the range lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{'#__range': [1, 2]})

        # Only the books are here as it is the first queryset.
        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        expected = [
            # Just the Articles.
            'Fiction',
            'Biography',
        ]
        self.assertEqual(data, expected)

    def test_queryset_unsupported(self):
        """Try excluding the QuerySets by a lookup that doesn't make sense."""
        with self.assertRaises(ValueError):
            self._get_qss().exclude(**{'#__year': 1})

    def test_empty(self):
        """Calling exclude on an empty QuerySetSequence doesn't error."""
        self.empty.exclude(title='')


class TestExtraAnnotate(TestBase):
    def test_extra(self):
        """Calling extra() gets applied to each QuerySet."""
        # Filter to just Bob's work.
        with self.assertNumQueries(0):
            bob_qss = self.all.extra(where=["author_id = '{}'".format(self.bob.id)])
        with self.assertNumQueries(2):
            self.assertEqual(bob_qss.count(), 3)

    def test_annotate(self):
        """Annotating should get applied to each QuerySet."""
        qss = QuerySetSequence(Publisher.objects.all(), PeriodicalPublisher.objects.all())
        qss = qss.annotate(published_count=Count('published'))

        # Each Published gets the count of things in it added.
        with self.assertNumQueries(2):
            data = [it.published_count for it in qss]
        self.assertEquals(data, [0, 2, 3])


class TestOrderBy(TestBase):
    def test_order_by(self):
        """Ensure that order_by() propagates to QuerySets and iteration."""
        # Order by author and ensure it takes.
        with self.assertNumQueries(0):
            qss = self.all.order_by('title')

        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, sorted(self.TITLES_BY_PK))

    def test_order_by_non_existent_field(self):
        """Ordering by a non-existent field raises an exception upon evaluation."""
        with self.assertNumQueries(0):
            qss = self.all.order_by('pages')
        with self.assertRaises(FieldError):
            list(qss)

    def test_order_by_multi(self):
        """Test ordering by multiple fields."""
        # Add another object with the same title, but a later release date.
        Book.objects.create(title="Fiction", author=self.alice,
                            publisher=self.big_books, pages=1,
                            release=date(2018, 10, 3))

        with self.assertNumQueries(0):
            qss = self.all.order_by('title', '-release')

        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            'Alice in Django-land',
            'Biography',
            'Django Rocks',
            'Fiction',
            'Fiction',
            'Some Article',
        ]
        self.assertEqual(data, expected)

    def test_order_by_multi_2(self):
        """Test ordering by multiple fields, where # is not first."""
        # Add another object with the same title, but in a different QuerySet.
        Article.objects.create(title="Fiction", author=self.alice,
                               publisher=self.mad_magazine,
                               release=date(2018, 10, 3))

        with self.assertNumQueries(0):
            qss = self.all.order_by('title', '-#')

        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = [(it.title, it.__class__.__name__) for it in qss]
        expected = [
            ('Alice in Django-land', 'Article'),
            ('Biography', 'Book'),
            ('Django Rocks', 'Article'),
            ('Fiction', 'Article'),
            ('Fiction', 'Book'),
            ('Some Article', 'Article'),
        ]
        self.assertEqual(data, expected)

    def test_order_by_relation(self):
        """
        Apply order_by() with a field that is a relation to another model's id.
        """
        # Order by author and ensure it takes.
        with self.assertNumQueries(0):
            qss = self.all.order_by('author_id')

        # The first two should be Alice, followed by three from Bob.
        with self.assertNumQueries(2):
            for expected, element in zip([self.alice.id] * 2 + [self.bob.id] * 3, qss):
                self.assertEqual(element.author_id, expected)

    def test_order_by_relation_pk(self):
        """
        Apply order_by() with a field that returns a model without a default
        ordering (i.e. using the pk).
        """
        # Order by publisher and ensure it takes.
        with self.assertNumQueries(0):
            qss = self.all.order_by('publisher')

        # Ensure that the test has any hope of passing.
        self.assertLess(self.mad_magazine.pk, self.big_books.pk)

        # The first three should be from Mad Magazine, followed by three from
        # Big Books.
        # Note that the QuerySetSequence itself needs the publisher objects to
        # compare them, so they all get pulled in.
        with self.assertNumQueries(2 + 5):
            for expected, element in zip([self.mad_magazine.id] * 3 + [self.big_books.id] * 2, qss):
                self.assertEqual(element.publisher.id, expected)

    def test_order_by_relation_with_ordering(self):
        """
        Apply order_by() with a field that returns a model with a default
        ordering.
        """
        # Order by author and ensure it takes.
        with self.assertNumQueries(0):
            qss = self.all.order_by('author')

        # The first two should be Alice, followed by three from Bob.
        # Note that the QuerySetSequence itself needs the author objects to
        # compare them, so they all get pulled in.
        with self.assertNumQueries(2 + 5):
            for expected, element in zip([self.alice.id] * 2 + [self.bob.id] * 3, qss):
                self.assertEqual(element.author.id, expected)

    def test_order_by_relation_with_different_ordering(self):
        """
        Apply order_by() with a field that returns a model with different
        ordering on sub-QuerySets.
        """
        # Both of these have publishers with the same fields, but different
        # ordering.
        all = QuerySetSequence(Article.objects.all(), BlogPost.objects.all())

        # Order by publisher and ensure it takes.
        with self.assertNumQueries(0):
            qss = all.order_by('publisher')

        with self.assertRaises(FieldError):
            list(qss)

    def test_order_by_relation_field(self):
        """Apply order_by() with a field through a model relationship."""
        # Order by author name and ensure it takes.
        with self.assertNumQueries(0):
            qss = self.all.order_by('author__name')

        # The first two should be Alice, followed by three from Bob.
        # Note that the QuerySetSequence itself needs the author objects to
        # compare them, so they all get pulled in.
        with self.assertNumQueries(2 + 5):
            for expected, element in zip([self.alice.id] * 2 + [self.bob.id] * 3, qss):
                self.assertEqual(element.author.id, expected)

    def test_order_by_relation_no_existent_field(self):
        """Apply order_by() with a field through a model relationship that doesn't exist."""
        with self.assertNumQueries(0):
            qss = self.all.order_by('publisher__address')

        with self.assertRaises(FieldError):
            list(qss)

    def test_order_by_queryset(self):
        """Ensure we can order by QuerySet and then other fields."""
        # Order by title, but don't interleave each QuerySet.
        with self.assertNumQueries(0):
            qss = self.all.order_by('#', 'title')

        # Ensure that _ordered_iterator isn't called.
        with patch('queryset_sequence.QuerySequenceIterable._ordered_iterator',
                   side_effect=AssertionError('_ordered_iterator should not be called')):
            # Check the titles are properly ordered.
            data = [it.title for it in qss]
            expected = [
                # First the Books, in order.
                'Biography',
                'Fiction',
                # Then the Articles, in order.
                'Alice in Django-land',
                'Django Rocks',
                'Some Article',
            ]
            self.assertEqual(data, expected)

    def test_order_by_queryset_reverse(self):
        """
        It is possible to reverse the order of the internal QuerySets.

        Note that this is *NOT* the same as calling reverse(), as that reverses
        the contents of each QuerySet as well.
        """
        # Order by title, but don't interleave each QuerySet. And reverse
        # QuerySets.
        with self.assertNumQueries(0):
            qss = self.all.order_by('-#', 'title')

        # Ensure that _ordered_iterator isn't called.
        with patch('queryset_sequence.QuerySequenceIterable._ordered_iterator',
                   side_effect=AssertionError('_ordered_iterator should not be called')):
            # Check the titles are properly ordered.
            data = [it.title for it in qss]
            expected = [
                # The articles, in order.
                'Alice in Django-land',
                'Django Rocks',
                'Some Article',
                # Then the Books, in order.
                'Biography',
                'Fiction',
            ]
            self.assertEqual(data, expected)

    def test_empty(self):
        """Calling order_by on an empty QuerySetSequence doesn't error."""
        self.empty.order_by('author')


class TestReverse(TestBase):
    def test_reverse(self):
        """Ensure calling reverse() returns elements in a reverse order."""
        # This really only makes sense if there's an order set.
        with self.assertNumQueries(0):
            qss = self.all.reverse()

        # Note that this didn't really reverse everything because no ordering
        # was set.
        expected = [
            "Django Rocks",
            "Alice in Django-land",
            "Some Article",

            "Fiction",
            "Biography",
        ]

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, expected)

    def test_reverse_twice(self):
        """Ensure calling reverse() twice returns elements in a normal order."""
        with self.assertNumQueries(0):
            qss = self.all.reverse().reverse()

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, self.TITLES_BY_PK)

    def test_reverse_ordered(self):
        """Reversing an ordered QuerySet should reverse the ordering too."""
        with self.assertNumQueries(0):
            qss = self.all.order_by('title').reverse()

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, sorted(self.TITLES_BY_PK, reverse=True))

    def test_reverse_twice_ordered(self):
        """Calling reverse() twice is negated, but then order by title."""
        with self.assertNumQueries(0):
            qss = self.all.reverse().order_by('title').reverse()

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, sorted(self.TITLES_BY_PK))

    def test_empty(self):
        """Calling reverse on an empty QuerySetSequence doesn't error."""
        self.empty.reverse()


class TestSlicing(TestBase):
    """Test indexing and slicing."""

    # TODO Caching throughout these test-cases.

    def test_single_element(self):
        """Single element."""
        # 2 counts + evaluating one QuerySet.
        with self.assertNumQueries(3):
            result = self.all[0]
        self.assertEqual(result.title, 'Fiction')
        self.assertIsInstance(result, Book)

    def test_one_QuerySet(self):
        """Test slicing only from one QuerySet."""
        with self.assertNumQueries(0):
            qss = self.all[0:2]

        # 2 counts + evaluating one QuerySet.
        with self.assertNumQueries(3):
            data = [it.title for it in qss]
        self.assertEqual(['Fiction', 'Biography'], data)

    def test_cast_list(self):
        """Test slicing and casting to a list."""
        with self.assertNumQueries(0):
            qss = self.all[0:2]

        # 2 counts + evaluating one QuerySet.
        with self.assertNumQueries(3):
            result = list(qss)
            data = [it.title for it in result]
        self.assertEqual(['Fiction', 'Biography'], data)

    def test_multiple_QuerySets(self):
        """Test slicing across elements from multiple QuerySets."""
        # 2 counts + 2 evaluations.
        with self.assertNumQueries(0):
            qss = self.all[1:3]

        # 2 counts + evaluating two QuerySets.
        with self.assertNumQueries(4):
            data = [it.title for it in qss]
        self.assertEqual(['Biography', 'Django Rocks'], data)

    def test_multiple_slices(self):
        """Test multiple slices taken."""
        with self.assertNumQueries(0):
            result = self.all[1:3]
        self.assertIsInstance(result, QuerySetSequence)
        # Evaluate the QuerySet.
        with self.assertNumQueries(3):
            article = result[1]
        self.assertEqual(article.title, 'Django Rocks')

    def test_multiple_slices_complex(self):
        """Test taking slices multiple times."""
        with self.assertNumQueries(0):
            qss = self.all[1:4]
        self.assertIsInstance(qss, QuerySetSequence)

        with self.assertNumQueries(0):
            qss = qss[1:2]

        # Evaluate the QuerySet.
        with self.assertNumQueries(3):
            data = [it.title for it in qss]
        self.assertEqual(data, ['Django Rocks'])

    def test_step(self):
        """Test behavior when a step is provided to the slice."""
        with self.assertNumQueries(4):
            qss = self.all[0:4:2]
            data = [it.title for it in qss]
        self.assertIsInstance(qss, list)

        self.assertEqual(['Fiction', 'Django Rocks'], data)

    def test_all(self):
        """Test slicing to all elements."""
        with self.assertNumQueries(0):
            qss = self.all[:]
        self.assertIsInstance(qss, QuerySetSequence)

        # Evaluate the QuerySet.
        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, self.TITLES_BY_PK)

    def test_slicing_order_by(self):
        """Test slicing when order_by has already been called."""
        # Order by author and take a slice.
        with self.assertNumQueries(0):
            qss = self.all.order_by('title')[1:3]
        self.assertIsInstance(qss, QuerySetSequence)

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data[0], 'Biography')
        self.assertEqual(data[1], 'Django Rocks')

    def test_open_slice(self):
        """Test slicing without an end."""
        qss = QuerySetSequence(Article.objects.all())[1:]

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(['Alice in Django-land', 'Some Article'], data)

    def test_closed_slice_single_qs(self):
        """Test slicing if the start and end are within the same QuerySet."""
        Article.objects.create(title='Another Article', author=self.bob,
                               publisher=self.mad_magazine,
                               release=date(2018, 10, 3))

        qss = QuerySetSequence(Article.objects.all())[1:3]

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(['Alice in Django-land', 'Some Article'], data)

    def test_empty(self):
        """Slicing an empty QuerySetSequence doesn't error."""
        self.assertEqual(list(self.empty[:]), [])


class TestGet(TestBase):
    def test_get(self):
        """
        Ensure that get() returns the expected element or raises DoesNotExist.
        """
        # Get a particular item.
        with self.assertNumQueries(2):
            book = self.all.get(title='Biography')
        self.assertEqual(book.title, 'Biography')
        self.assertIsInstance(book, Book)

    def test_not_found(self):
        # An exception is rasied if get() is called and nothing is found.
        with self.assertNumQueries(2):
            with self.assertRaises(ObjectDoesNotExist):
                self.all.get(title='')

    def test_multi_found(self):
        """Test multiple found in the same QuerySet."""
        # ...or if get() is called and multiple objects are found.
        with self.assertNumQueries(1):
            with self.assertRaises(MultipleObjectsReturned):
                self.all.get(author=self.bob)

    def test_multi_found_separate_querysets(self):
        """Test one found in each QuerySet."""
        # ...or if get() is called and multiple objects are found.
        with self.assertNumQueries(2):
            with self.assertRaises(MultipleObjectsReturned):
                self.all.get(title__contains='A')

    def test_related_model(self):
        qss = QuerySetSequence(Article.objects.all(), BlogPost.objects.all())
        with self.assertNumQueries(2):
            post = qss.get(publisher__name="Wacky Website")
        self.assertEqual(post.title, 'Post')
        self.assertIsInstance(post, BlogPost)

    def test_queryset_lookup(self):
        """Test using the special QuerySet lookup."""
        with self.assertNumQueries(1):
            article = self.all.get(**{'#': 1, 'author': self.bob})
        self.assertEqual(article.title, 'Some Article')
        self.assertIsInstance(article, Article)

    def test_empty(self):
        """Calling get on an empty QuerySetSequence raises ObjectDoesNotExist."""
        with self.assertRaises(ObjectDoesNotExist):
            self.empty.get(pk=1)


class TestBoolean(TestBase):
    """Tests related to casting the QuerySetSequence to a boolean."""
    def test_exists(self):
        """Ensure that it casts to True if the item is found."""
        with self.assertNumQueries(2):
            self.assertTrue(self.all.filter(title='Biography'))

    def test_exists_second(self):
        """Ensure that it casts to True if the item is found in a subsequent QuerySet."""
        with self.assertNumQueries(2):
            self.assertTrue(self.all.filter(title='Alice in Django-land'))

    def test_not_found(self):
        """Ensure that exists() returns False if the item is not found."""
        with self.assertNumQueries(2):
            self.assertFalse(self.all.filter(title=''))

    def test_multi_found(self):
        """Ensure that it casts to True if multiple items are found."""
        with self.assertNumQueries(2):
            self.assertTrue(self.all.filter(author=self.bob))

    def test_empty(self):
        """An empty QuerySetSequence should resolve to False."""
        self.assertFalse(self.empty)


class TestEarliestLatest(TestBase):
    def test_earliest(self):
        """The earliest release overall should be returned."""
        with self.assertNumQueries(2):
            earliest = self.all.earliest('release')
        self.assertEqual(earliest.title, 'Some Article')

    def test_latest(self):
        """The latest release overall should be returned."""
        with self.assertNumQueries(2):
            latest = self.all.latest('release')
        self.assertEqual(latest.title, 'Biography')

    @skipIf(django.VERSION < (2, 0), 'Support for reversed calls to earliest() and latest() was added in Django 2.0')
    def test_earliest_reverse(self):
        """The earliest release overall reversed is the latest."""
        with self.assertNumQueries(2):
            earliest = self.all.earliest('-release')
        self.assertEqual(earliest.title, 'Biography')

    @skipIf(django.VERSION < (2, 0), 'Support for reversed calls to earliest() and latest() was added in Django 2.0')
    def test_latest_reverse(self):
        """The latest release overall reversed is the earliest."""
        with self.assertNumQueries(2):
            latest = self.all.latest('-release')
        self.assertEqual(latest.title, 'Some Article')

    def test_earliest_get_latest_by(self):
        """Not providing fields causes the get_latest_by field to be used."""
        with self.assertNumQueries(2):
            latest = self.all.earliest()
        self.assertEqual(latest.title, 'Some Article')

    def test_earliest_get_latest_by_error(self):
        """When get_latest_by is used, they must all be the same."""
        with self.assertRaises(ValueError):
            QuerySetSequence(Book.objects.all(), BlogPost.objects.all()).earliest()

    def test_latest_get_latest_by(self):
        """Not providing fields causes the get_latest_by field to be used."""
        with self.assertNumQueries(2):
            latest = self.all.latest()
        self.assertEqual(latest.title, 'Biography')

    def test_latest_get_latest_by_error(self):
        """When get_latest_by is used, they must all be the same."""
        with self.assertRaises(ValueError):
            QuerySetSequence(Book.objects.all(), BlogPost.objects.all()).latest()

    def test_empty(self):
        """An empty QuerySetSequence raises a ValueError."""
        with self.assertRaises(ValueError):
            self.empty.latest()

        with self.assertRaises(ValueError):
            self.empty.earliest()


class TestFirstLast(TestBase):
    def test_first_unordered(self):
        """Should return the first element of the first QuerySet."""
        with self.assertNumQueries(1):
            self.assertEqual(self.all.first().title, 'Fiction')

    def test_last_unordered(self):
        """Should return the last element of the last QuerySet."""
        with self.assertNumQueries(1):
            self.assertEqual(self.all.last().title, 'Some Article')

    def test_empty(self):
        """Empty QuerySetSequence should work."""
        self.assertIsNone(self.empty.first())
        self.assertIsNone(self.empty.last())

    def test_first_ordered(self):
        """When ordering, the items of each QuerySet must be compared."""
        # Order by author and ensure it takes.
        with self.assertNumQueries(2):
            self.assertEqual(self.all.order_by('title').first().title, 'Alice in Django-land')

        with self.assertNumQueries(2):
            self.assertEqual(self.all.order_by('-title').first().title, 'Some Article')

    def test_last_ordered(self):
        """When ordering, the items of each QuerySet must be compared."""
        # Order by author and ensure it takes.
        with self.assertNumQueries(2):
            self.assertEqual(self.all.order_by('-title').last().title, 'Alice in Django-land')

        with self.assertNumQueries(2):
            self.assertEqual(self.all.order_by('title').last().title, 'Some Article')


class TestExists(TestBase):
    def test_exists(self):
        """Ensure that exists() returns True if the item is found in the first QuerySet."""
        with self.assertNumQueries(1):
            self.assertTrue(self.all.filter(title='Biography').exists())

    def test_exists_second(self):
        """Ensure that exists() returns True if the item is found in a subsequent QuerySet."""
        with self.assertNumQueries(2):
            self.assertTrue(self.all.filter(title='Alice in Django-land').exists())

    def test_not_found(self):
        """Ensure that exists() returns False if the item is not found."""
        with self.assertNumQueries(2):
            self.assertFalse(self.all.filter(title='').exists())

    def test_multi_found(self):
        """Ensure that exists() returns True if multiple items are found."""
        with self.assertNumQueries(1):
            self.assertTrue(self.all.filter(author=self.bob).exists())

    def test_empty(self):
        """An empty QuerySetSequence should return False."""
        self.assertFalse(self.empty.exists())


class TestUpdate(TestBase):
    def test_update(self):
        """Update should apply across all QuerySets."""
        # The queries are: creating a save point, the two updates, releasing the
        # save point.
        with self.assertNumQueries(4):
            result = self.all.update(title='A New Title')
        self.assertEqual(result, 5)

        with self.assertNumQueries(2):
            data = [it.title for it in self.all]
        self.assertEqual(data, ['A New Title'] * 5)

    def test_error(self):
        """If an error occurs on one of the QuerySets, no changes should occur."""
        # The queries are: creating a save point, attempting the two updates,
        # releasing the save point.
        with self.assertNumQueries(4):
            with self.assertRaises(FieldDoesNotExist):
                self.all.update(pages=8)

        # The page counts for the Book objects are unmodified.
        with self.assertNumQueries(1):
            data = [it.pages for it in Book.objects.all()]
        self.assertEqual(data, [10, 20])

    def test_empty(self):
        """Calling delete on an empty QuerySetSequence should work."""
        result = self.empty.update()
        self.assertEqual(result, 0)


class TestDelete(TestBase):
    def test_delete_all(self):
        """Ensure that delete() works properly."""
        with self.assertNumQueries(2):
            result = self.all.delete()
        self.assertEqual(result[0], 5)
        self.assertEqual(result[1], {'tests.Article': 3, 'tests.Book': 2})

        with self.assertNumQueries(2):
            self.assertEqual(self.all.count(), 0)

    def test_delete_filter(self):
        """Ensure that delete() works properly when filtering."""
        with self.assertNumQueries(2):
            result = self.all.filter(author=self.alice).delete()
        self.assertEqual(result[0], 2)
        self.assertEqual(result[1], {'tests.Article': 2, 'tests.Book': 0})

        with self.assertNumQueries(2):
            self.assertEqual(self.all.count(), 3)

    def test_empty(self):
        """Calling delete on an empty QuerySetSequence should work."""
        result = self.empty.delete()
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], {})


class TestExplain(TestBase):
    @skipIf(django.VERSION >= (2, 1), 'explain() added in Django 2.1')
    def test_not_supported(self):
        """Older versions of Django raise an attribute error."""
        with self.assertRaises(AttributeError):
            self.all.explain()

    @skipIf(django.VERSION < (2, 1), 'explain() added in Django 2.1')
    def test_supported(self):
        """Supported versions of Django support explain() and return a string."""
        with self.assertNumQueries(2):
            explanation = self.all.explain()
        # The output of explain is not guaranteed, so do some rough checks.
        self.assertEqual(len(explanation.split('\n')), 2)


class TestGetQueryset(TestBase):
    """Tests related to retrieving QuerySets from the sequence."""
    def test_get_querysets(self):
        """Ensure the correct QuerySet objects are returned."""
        querysets = [Book.objects.all(), Article.objects.all()]
        matched_qss = QuerySetSequence(*querysets)

        self.assertEqual(querysets, matched_qss.get_querysets())


class TestCannotImplement(TestCase):
    """The following methods cannot be implemented in QuerySetSequence."""
    def setUp(self):
        self.all = QuerySetSequence()

    def test_create(self):
        with self.assertRaises(NotImplementedError):
            self.all.create()

    def test_get_or_create(self):
        with self.assertRaises(NotImplementedError):
            self.all.get_or_create()

    def test_update_or_create(self):
        with self.assertRaises(NotImplementedError):
            self.all.update_or_create()

    def test_bulk_create(self):
        with self.assertRaises(NotImplementedError):
            self.all.bulk_create([])

    def test_in_bulk(self):
        with self.assertRaises(NotImplementedError):
            self.all.in_bulk()


class TestNotImplemented(TestCase):
    """The following methods have not been implemented in QuerySetSequence."""
    def setUp(self):
        self.all = QuerySetSequence()

    def test_distinct(self):
        with self.assertRaises(NotImplementedError):
            self.all.distinct()

    def test_values(self):
        with self.assertRaises(NotImplementedError):
            self.all.values()

    def test_values_list(self):
        with self.assertRaises(NotImplementedError):
            self.all.values_list()

    def test_dates(self):
        with self.assertRaises(NotImplementedError):
            self.all.dates(None, None)

    def test_datetimes(self):
        with self.assertRaises(NotImplementedError):
            self.all.datetimes(None, None)

    def test_union(self):
        with self.assertRaises(NotImplementedError):
            self.all.union()

    def test_intersection(self):
        with self.assertRaises(NotImplementedError):
            self.all.intersection()

    def test_difference(self):
        with self.assertRaises(NotImplementedError):
            self.all.difference()

    def test_select_for_update(self):
        with self.assertRaises(NotImplementedError):
            self.all.select_for_update()

    def test_raw(self):
        with self.assertRaises(NotImplementedError):
            self.all.raw()

    def test_aggregate(self):
        with self.assertRaises(NotImplementedError):
            self.all.aggregate()
