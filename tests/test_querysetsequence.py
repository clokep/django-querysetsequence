from __future__ import unicode_literals

from django.core.exceptions import (FieldError, MultipleObjectsReturned,
                                    ObjectDoesNotExist)
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
                               publisher=mad_magazine)
        Article.objects.create(title="Alice in Django-land", author=alice,
                               publisher=mad_magazine)

        # Bob wrote a couple of books, an article, and a blog post.
        Book.objects.create(title="Fiction", author=bob, publisher=big_books,
                            pages=10)
        Book.objects.create(title="Biography", author=bob, publisher=big_books,
                            pages=20)
        Article.objects.create(title="Some Article", author=bob,
                               publisher=mad_magazine)
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


class TestIterator(TestBase):
    """Test the iterator when no ordering is set."""
    EXPECTED = [
        "Fiction",
        "Biography",
        "Django Rocks",
        "Alice in Django-land",
        "Some Article",
    ]

    def test_iterator(self):
        """Ensure that an iterator queries for the results."""
        # Ensure that calling iterator twice re-evaluates the query.
        with self.assertNumQueries(2):
            data = [it.title for it in self.all.iterator()]
        self.assertEqual(data, TestIterator.EXPECTED)

        with self.assertNumQueries(2):
            data = [it.title for it in self.all.iterator()]
        self.assertEqual(data, TestIterator.EXPECTED)

    def test_iter(self):
        """Directly iteratoring the query should return the same results."""
        with self.assertNumQueries(2):
            data = [it.title for it in self.all]
        self.assertEqual(data, TestIterator.EXPECTED)

    def test_iter_cache(self):
        """Ensure that iterating the QuerySet caches."""
        with self.assertNumQueries(2):
            data = [it.title for it in self.all]
            self.assertEqual(data, TestIterator.EXPECTED)

        # So the second call does nothing.
        with self.assertNumQueries(0):
            data = [it.title for it in self.all]
            self.assertEqual(data, TestIterator.EXPECTED)

    def test_empty(self):
        """Test an empty iteration."""
        qss = QuerySetSequence()
        with self.assertNumQueries(0):
            self.assertEqual(list(qss), [])

    def test_empty_subqueryset(self):
        """Iterating an empty set should work."""
        qss = QuerySetSequence(Book.objects.all(), Article.objects.none()).order_by('title')

        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        self.assertEqual(data, ['Biography', 'Fiction'])


class TestNone(TestBase):
    def test_none(self):
        """
        Ensure an instance of EmptyQuerySet is returned and has no results (and
        doesn't perform queries).
        """
        with self.assertNumQueries(0):
            qss = self.all.none()
            data = list(qss)

        # This returns a special EmptyQuerySet.
        self.assertIsInstance(qss, EmptyQuerySet)

        # Should have no data.
        self.assertEqual(data, [])

    def test_count(self):
        """An empty QuerySet should have no data."""
        with self.assertNumQueries(0):
            qss = self.all.none()

            self.assertEqual(qss.count(), 0)
            self.assertEqual(len(qss), 0)


class TestAll(TestBase):
    def test_all(self):
        """Ensure a copy is made when calling all()."""
        copy = self.all.all()

        # Different QuerySetSequences, but the same content.
        self.assertNotEqual(self.all, copy)
        # Ordered by sub-QuerySet than by pk.
        expected = [
            "Fiction",
            "Biography",
            "Django Rocks",
            "Alice in Django-land",
            "Some Article",
        ]

        # Each QuerySet should be evaluated separately.
        with self.assertNumQueries(2):
            data = [it.title for it in self.all]
        self.assertEqual(data, expected)

        with self.assertNumQueries(2):
            data = [it.title for it in copy]
        self.assertEqual(data, expected)


class TestSelectRelated(TestBase):
    # Bob, Bob, Alice, Alice, Bob.
    EXPECTED_ORDER = [2, 2, 1, 1, 2]

    def test_no_select_related(self):
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


class TestPrefetchRelated(TestBase):
    # Bob, Bob, Alice, Alice, Bob.
    EXPECTED_ORDER = [2, 2, 1, 1, 2]

    def test_no_prefetch_related(self):
        """Check behavior first, one database query per author access."""
        with self.assertNumQueries(2):
            books = list(self.all)
        with self.assertNumQueries(5):
            authors = [b.author.id for b in books]
        self.assertEqual(authors, self.EXPECTED_ORDER)

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
        expected = [
            # The Books and Articles.
            'Fiction',
            'Biography',
            'Django Rocks',
            'Alice in Django-land',
            'Some Article',
        ]
        self.assertEqual(data, expected)

    def test_queryset_lte(self):
        """Test filtering the QuerySets by <= lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{'#__lte': 1})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            # The Books and Articles.
            'Fiction',
            'Biography',
            'Django Rocks',
            'Alice in Django-land',
            'Some Article',
        ]
        self.assertEqual(data, expected)

    def test_queryset_in(self):
        """Filter the QuerySets with the in lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{'#__in': [1]})

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
            # Just the Articles.
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
        expected = [
            # The Books and Articles.
            'Fiction',
            'Biography',
            'Django Rocks',
            'Alice in Django-land',
            'Some Article',
        ]
        self.assertEqual(data, expected)

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


class TestOrderBy(TestBase):
    def test_order_by(self):
        """Ensure that order_by() propagates to QuerySets and iteration."""
        # Order by author and ensure it takes.
        with self.assertNumQueries(0):
            qss = self.all.order_by('title')

        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            'Alice in Django-land',
            'Biography',
            'Django Rocks',
            'Fiction',
            'Some Article',
        ]
        self.assertEqual(data, expected)

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
                            publisher=self.big_books, pages=1)

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
                               publisher=self.mad_magazine)

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

        expected = [
            "Fiction",
            "Biography",
            "Django Rocks",
            "Alice in Django-land",
            "Some Article",
        ]
        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, expected)

    def test_reverse_ordered(self):
        """Reversing an ordered QuerySet should reverse the ordering too."""
        with self.assertNumQueries(0):
            qss = self.all.order_by('title').reverse()

        expected = [
            "Some Article",
            "Fiction",
            "Django Rocks",
            "Biography",
            "Alice in Django-land",
        ]

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, expected)

    def test_reverse_twice_ordered(self):
        with self.assertNumQueries(0):
            qss = self.all.reverse().order_by('title').reverse()

        expected = [
            "Alice in Django-land",
            "Biography",
            "Django Rocks",
            "Fiction",
            "Some Article",
        ]

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, expected)


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
        qss = self.all[:]
        self.assertIsInstance(qss, QuerySetSequence)

        # No data evaluated.
        with self.assertNumQueries(2):
            self.assertEqual(len(qss), 5)

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
                               publisher=self.mad_magazine)

        qss = QuerySetSequence(Article.objects.all())[1:3]

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(['Alice in Django-land', 'Some Article'], data)


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


class TestBoolean(TestBase):
    """Tests related to casting the QuerySetSequence to a boolean."""
    def test_exists(self):
        """Ensure that it casts to True if the item is found."""
        with self.assertNumQueries(2):
            self.assertTrue(self.all.filter(title='Biography'))

    def test_exists_second(self):
        """Ensure that it casts to True if the item is found in a subsequent QuerySet."""
        with self.assertNumQueries(2):
            self.assertTrue(self.all.filter(title="Alice in Django-land"))

    def test_not_found(self):
        """Ensure that exists() returns False if the item is not found."""
        with self.assertNumQueries(2):
            self.assertFalse(self.all.filter(title=''))

    def test_multi_found(self):
        """Ensure that it casts to True if multiple items are found."""
        with self.assertNumQueries(2):
            self.assertTrue(self.all.filter(author=self.bob))


class TestExists(TestBase):
    def test_exists(self):
        """Ensure that exists() returns True if the item is found in the first QuerySet."""
        with self.assertNumQueries(1):
            self.assertTrue(self.all.filter(title='Biography').exists())

    def test_exists_second(self):
        """Ensure that exists() returns True if the item is found in a subsequent QuerySet."""
        with self.assertNumQueries(2):
            self.assertTrue(self.all.filter(title="Alice in Django-land").exists())

    def test_not_found(self):
        """Ensure that exists() returns False if the item is not found."""
        with self.assertNumQueries(2):
            self.assertFalse(self.all.filter(title='').exists())

    def test_multi_found(self):
        """Ensure that exists() returns True if multiple items are found."""
        with self.assertNumQueries(1):
            self.assertTrue(self.all.filter(author=self.bob).exists())


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
