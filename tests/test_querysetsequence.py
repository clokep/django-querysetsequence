from datetime import date, datetime, timezone
from unittest import skipIf
from unittest.mock import patch

import django
from asgiref.sync import sync_to_async
from django import forms
from django.core.exceptions import (
    FieldDoesNotExist,
    FieldError,
    MultipleObjectsReturned,
    ObjectDoesNotExist,
)
from django.db import connection, transaction
from django.db.models import Avg, Count, Max, Min, Q, StdDev, Sum, Variance
from django.db.models.query import EmptyQuerySet
from django.test import TestCase
from django.utils.timezone import make_aware

from queryset_sequence import QuerySetSequence
from tests.models import (
    Article,
    Author,
    BlogPost,
    Book,
    OnlinePublisher,
    PeriodicalPublisher,
    Publisher,
)

if django.VERSION >= (4, 1):
    ImplementedIn41 = NotImplementedError
else:
    ImplementedIn41 = AttributeError


class TestBase(TestCase):
    # The title of each Book, followed by each Article; each ordered by primary
    # key. This matches all without any transforms applied.
    TITLES_BY_PK = [
        "Fiction",
        "Biography",
        "Django Rocks",
        "Alice in Django-land",
        "Some Article",
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
        big_books = Publisher.objects.create(name="Big Books", address="123 Street")
        wacky_website = OnlinePublisher.objects.create(name="Wacky Website")

        # Alice wrote some articles.
        Article.objects.create(
            title="Django Rocks",
            author=alice,
            publisher=mad_magazine,
            release=date(1980, 4, 21),
        )
        Article.objects.create(
            title="Alice in Django-land",
            author=alice,
            publisher=mad_magazine,
            release=date(1990, 8, 14),
        )

        # Bob wrote a couple of books, an article, and a blog post.
        book = Book.objects.create(
            title="Fiction", author=bob, pages=10, release=date(2001, 6, 12)
        )
        book.publishers.set([big_books])
        book = Book.objects.create(
            title="Biography",
            author=bob,
            pages=20,
            release=date(2002, 12, 24),
        )
        book.publishers.set([big_books])
        Article.objects.create(
            title="Some Article",
            author=bob,
            publisher=mad_magazine,
            release=date(1979, 1, 1),
        )
        BlogPost.objects.create(
            title="Post",
            author=bob,
            publisher=wacky_website,
            published=make_aware(datetime(2003, 5, 1, 12, 0)),
        )

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

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_acount(self):
        # The proper length should be returned via database queries.
        self.assertEqual(await self.all.acount(), 5)

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

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_acount_slice(self):
        """Ensure the proper length is calculated when a slice is taken."""
        self.assertEqual(await self.all[1:].acount(), 4)

    def test_empty_count(self):
        """An empty QuerySetSequence has a count of 0."""
        self.assertEqual(self.empty.count(), 0)

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_acount_empty_count(self):
        """An empty QuerySetSequence has a count of 0."""
        self.assertEqual(await self.empty.acount(), 0)

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
        qss = QuerySetSequence(Book.objects.all(), Article.objects.none()).order_by(
            "title"
        )

        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        self.assertEqual(data, ["Biography", "Fiction"])


class TestOperators(TestBase):
    def test_and_identity(self):
        """ANDing with an EmptyQuerySet returns an EmptyQuerySet."""
        with self.assertNumQueries(0):
            combined = self.all & BlogPost.objects.none()
        self.assertIsInstance(combined, EmptyQuerySet)

    def test_and(self):
        """
        ANDing with a QuerySet applies the and to each QuerySet and removes ones
        of differing types.
        """
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
        self.assertEqual(data, ["Fiction"])

    def test_empty_and(self):
        """
        An empty QuerySetSequence can be ANDed with a QuerySet, but returns an
        EmptyQuerySet.
        """
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
        self.assertEqual(data, self.TITLES_BY_PK + ["Post"])

    def test_or_querysetsequence(self):
        """ORing with a QuerySetSequence should combine the lists of QuerySets."""
        with self.assertNumQueries(0):
            combined = self.all | QuerySetSequence(BlogPost.objects.all())
        self.assertIsInstance(combined, QuerySetSequence)
        self.assertEqual(len(combined._querysets), 3)

        with self.assertNumQueries(3):
            data = [it.title for it in combined.iterator()]
        self.assertEqual(data, self.TITLES_BY_PK + ["Post"])

    def test_empty_or(self):
        """
        An empty QuerySetSequence can be ORed with a QuerySet and returns an
        the original QuerySet.
        """
        combined = self.empty | BlogPost.objects.all()
        self.assertIsInstance(combined, QuerySetSequence)
        self.assertEqual(len(combined._querysets), 1)

        with self.assertNumQueries(1):
            data = [it.title for it in combined.iterator()]
        self.assertEqual(data, ["Post"])

    def test_empty_or_querysetsequence(self):
        combined = self.empty | QuerySetSequence(BlogPost.objects.all())
        self.assertIsInstance(combined, QuerySetSequence)
        self.assertEqual(len(combined._querysets), 1)

        with self.assertNumQueries(1):
            data = [it.title for it in combined.iterator()]
        self.assertEqual(data, ["Post"])


class TestDatesDatetimes(TestBase):
    def setUp(self):
        super().setUp()
        # A second BlogPost, so that datetimes() has more than one value to
        # interleave. Books and Articles share the "release" DateField and are
        # already enough to exercise the interleaving.
        BlogPost.objects.create(
            title="Older Post",
            author=self.bob,
            publisher=self.wacky_website,
            published=make_aware(datetime(1995, 2, 3, 8, 30)),
        )

    def test_dates(self):
        """dates() interleaves truncated dates from every QuerySet."""
        # Books sort after Articles even though the Books come first, so the
        # results are ordered across the sequence rather than concatenated.
        self.assertEqual(
            list(self.all.dates("release", "year")),
            [
                date(1979, 1, 1),
                date(1980, 1, 1),
                date(1990, 1, 1),
                date(2001, 1, 1),
                date(2002, 1, 1),
            ],
        )

    def test_dates_desc(self):
        """dates() honors descending ordering."""
        self.assertEqual(
            list(self.all.dates("release", "year", order="DESC")),
            [
                date(2002, 1, 1),
                date(2001, 1, 1),
                date(1990, 1, 1),
                date(1980, 1, 1),
                date(1979, 1, 1),
            ],
        )

    def test_dates_shared_across_querysets(self):
        """A date shared by two models is returned once per QuerySet."""
        # "Alice in Django-land" already has a 1990 release.
        Book.objects.create(
            title="Shared Release", author=self.bob, pages=30, release=date(1990, 1, 1)
        )
        self.assertEqual(
            list(self.all.dates("release", "year")),
            [
                date(1979, 1, 1),
                date(1980, 1, 1),
                date(1990, 1, 1),
                date(1990, 1, 1),
                date(2001, 1, 1),
                date(2002, 1, 1),
            ],
        )

    def test_dates_slicing(self):
        """dates() supports slicing across the whole sequence."""
        qss = self.all.dates("release", "year")
        self.assertEqual(list(qss[1:3]), [date(1980, 1, 1), date(1990, 1, 1)])

    def test_dates_count(self):
        """count() counts truncated dates across the whole sequence."""
        self.assertEqual(self.all.dates("release", "year").count(), 5)

    def test_dates_excludes_nulls(self):
        """Django's dates() drops rows where the field is NULL."""
        Book.objects.create(title="Undated", author=self.bob, pages=30)
        self.assertEqual(
            list(self.all.dates("release", "year")),
            [
                date(1979, 1, 1),
                date(1980, 1, 1),
                date(1990, 1, 1),
                date(2001, 1, 1),
                date(2002, 1, 1),
            ],
        )

    def test_dates_empty(self):
        """dates() over an empty QuerySetSequence returns nothing."""
        self.assertEqual(list(self.empty.dates("release", "year")), [])

    def test_dates_invalid_kind(self):
        """Django rejects an unknown truncation."""
        with self.assertRaises(ValueError):
            list(self.all.dates("release", "century"))

    def test_dates_invalid_order(self):
        """Django rejects an unknown ordering."""
        with self.assertRaises(ValueError):
            list(self.all.dates("release", "year", order="SIDEWAYS"))

    def test_dates_missing_field(self):
        """A field missing from one QuerySet is an error."""
        qss = QuerySetSequence(Book.objects.all(), Author.objects.all())
        with self.assertRaises(FieldError):
            list(qss.dates("release", "year"))

    def test_datetimes(self):
        """datetimes() truncates datetimes from every QuerySet."""
        # Pass tzinfo explicitly so the results do not depend on TIME_ZONE.
        self.assertEqual(
            list(
                QuerySetSequence(BlogPost.objects.all()).datetimes(
                    "published", "year", tzinfo=timezone.utc
                )
            ),
            [
                datetime(1995, 1, 1, tzinfo=timezone.utc),
                datetime(2003, 1, 1, tzinfo=timezone.utc),
            ],
        )

    def test_datetimes_interleaved(self):
        """datetimes() interleaves truncated datetimes from every QuerySet."""
        # The 2003 posts come first but sort last.
        qss = QuerySetSequence(
            BlogPost.objects.filter(published__year=2003),
            BlogPost.objects.filter(published__year=1995),
        )
        self.assertEqual(
            list(qss.datetimes("published", "year", tzinfo=timezone.utc)),
            [
                datetime(1995, 1, 1, tzinfo=timezone.utc),
                datetime(2003, 1, 1, tzinfo=timezone.utc),
            ],
        )

    def test_datetimes_month(self):
        """datetimes() truncates to the requested kind."""
        self.assertEqual(
            list(
                QuerySetSequence(BlogPost.objects.all()).datetimes(
                    "published", "month", tzinfo=timezone.utc
                )
            ),
            [
                datetime(1995, 2, 1, tzinfo=timezone.utc),
                datetime(2003, 5, 1, tzinfo=timezone.utc),
            ],
        )

    def test_datetimes_desc(self):
        """datetimes() honors descending ordering."""
        self.assertEqual(
            list(
                QuerySetSequence(BlogPost.objects.all()).datetimes(
                    "published", "year", order="DESC", tzinfo=timezone.utc
                )
            ),
            [
                datetime(2003, 1, 1, tzinfo=timezone.utc),
                datetime(1995, 1, 1, tzinfo=timezone.utc),
            ],
        )

    def test_datetimes_excludes_nulls(self):
        """Django's datetimes() drops rows where the field is NULL."""
        BlogPost.objects.create(
            title="Unscheduled", author=self.bob, publisher=self.wacky_website
        )
        self.assertEqual(
            list(
                QuerySetSequence(BlogPost.objects.all()).datetimes(
                    "published", "year", tzinfo=timezone.utc
                )
            ),
            [
                datetime(1995, 1, 1, tzinfo=timezone.utc),
                datetime(2003, 1, 1, tzinfo=timezone.utc),
            ],
        )

    def test_datetimes_empty(self):
        """datetimes() over an empty QuerySetSequence returns nothing."""
        self.assertEqual(
            list(self.empty.datetimes("published", "year", tzinfo=timezone.utc)), []
        )

    def test_datetimes_no_is_dst(self):
        """is_dst was dropped along with Django's support for it."""
        qss = QuerySetSequence(BlogPost.objects.all())
        with self.assertRaises(TypeError):
            qss.datetimes("published", "year", is_dst=True)

    def test_datetimes_on_date_field(self):
        """Django refuses to truncate a DateField to a DateTimeField."""
        with self.assertRaises(ValueError):
            list(self.all.datetimes("release", "year"))


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

    def test_empty(self):
        qss = QuerySetSequence(model=Author).none()

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
    EXPECTED_ORDER = ["Bob", "Bob", "Alice", "Alice", "Bob"]

    def test_no_related(self):
        """Check the behavior to ensure that iterating causes additional queries."""
        with self.assertNumQueries(2):
            books = list(self.all)
        with self.assertNumQueries(5):
            authors = [b.author.name for b in books]
        self.assertEqual(authors, self.EXPECTED_ORDER)

    def test_select_related(self):
        """Select related removes subsequent queries to get ForeignKeys."""
        with self.assertNumQueries(2):
            books = list(self.all.select_related("author"))
        with self.assertNumQueries(0):
            authors = [b.author.name for b in books]
        self.assertEqual(authors, self.EXPECTED_ORDER)

    def test_select_related_multiple_fks(self):
        """Select related with multiple FKs on a single model."""
        # Article has both 'author' and 'publisher' FKs
        articles_qs = QuerySetSequence(Article.objects.all())
        with self.assertNumQueries(1):
            articles = list(articles_qs.select_related("author", "publisher"))
        with self.assertNumQueries(0):
            data = [(a.author.name, a.publisher.name) for a in articles]
        self.assertEqual(
            data,
            [
                ("Alice", "Mad Magazine"),
                ("Alice", "Mad Magazine"),
                ("Bob", "Mad Magazine"),
            ],
        )

    def test_clear_select_related(self):
        """Clearing select related causes all the database queries to occur again."""
        # Ensure there is a database query.
        with self.assertNumQueries(2):
            books = list(self.all.select_related("author").select_related(None))
        with self.assertNumQueries(5):
            authors = [b.author.name for b in books]
        self.assertEqual(authors, self.EXPECTED_ORDER)

    def test_empty_select_related(self):
        """Calling select_related on an empty QuerySetSequence doesn't error."""
        self.empty.select_related("author")

    def test_prefetch_related(self):
        """Now ensure one database query for all authors, per QuerySet."""
        with self.assertNumQueries(4):
            books = list(self.all.prefetch_related("author"))
        with self.assertNumQueries(0):
            authors = [b.author.name for b in books]
        self.assertEqual(authors, self.EXPECTED_ORDER)

    def test_prefetch_related_multiple_fks(self):
        """Prefetch related with multiple relations on a single model."""
        # Book has 'author' FK and 'publishers' M2M
        books_qs = QuerySetSequence(Book.objects.all())
        with self.assertNumQueries(3):
            books = list(books_qs.prefetch_related("author", "publishers"))
        with self.assertNumQueries(0):
            data = [
                (b.author.name, [p.name for p in b.publishers.all()]) for b in books
            ]
        self.assertEqual(
            data,
            [
                ("Bob", ["Big Books"]),
                ("Bob", ["Big Books"]),
            ],
        )

    def test_clear_prefetch_related(self):
        """Ensure the original behavior is restored if prefetch related is cleared."""
        with self.assertNumQueries(2):
            books = list(self.all.prefetch_related("author").prefetch_related(None))
        with self.assertNumQueries(5):
            authors = [b.author.name for b in books]
        self.assertEqual(authors, self.EXPECTED_ORDER)

    def test_empty_prefetch_related(self):
        """Calling prefetch_related on an empty QuerySetSequence doesn't error."""
        self.empty.prefetch_related("author")

    def test_model_choice_iterator(self):
        """Ensure that ModelChoiceField works for QuerySetSequence."""
        f = forms.ModelChoiceField(self.all)
        self.assertEqual(
            list(f.choices),
            [("", f.empty_label)] + [(it.pk, str(it)) for it in self.all],
        )


class TestDeferOnly(TestBase):
    def test_defer(self):
        """A deferred field will be loaded on access."""
        with self.assertNumQueries(2):
            books = list(self.all.defer("title"))
        with self.assertNumQueries(5):
            titles = [b.title for b in books]
        self.assertEqual(titles, self.TITLES_BY_PK)

    def test_clear_defer(self):
        """Ensure the original behavior is restored if defer is cleared."""
        with self.assertNumQueries(2):
            books = list(self.all.defer("title").defer(None))
        with self.assertNumQueries(0):
            titles = [b.title for b in books]
        self.assertEqual(titles, self.TITLES_BY_PK)

    def test_empty_defer(self):
        """Calling defer on an empty QuerySetSequence doesn't error."""
        self.empty.defer("title")

    def test_only(self):
        """Only causes other fields to load on access (opposite of defer)."""
        with self.assertNumQueries(2):
            books = list(self.all.only("author"))
        with self.assertNumQueries(5):
            titles = [b.title for b in books]
        self.assertEqual(titles, self.TITLES_BY_PK)

    # Note that you cannot clear an only call, so None is not a valid value.

    def test_order_by(self):
        """Ensure ordering still works when some fields are not included."""
        # Additional queries are due to the field needing to be pulled
        # individually during sorting.
        with self.assertNumQueries(7):
            books = list(self.all.only("author").order_by("title"))
        # No additional queries are necessary since the titles were used in
        # sorting.
        with self.assertNumQueries(0):
            titles = [b.title for b in books]
        self.assertEqual(titles, sorted(self.TITLES_BY_PK))

    def test_empty_only(self):
        """Calling only on an empty QuerySetSequence doesn't error."""
        self.empty.only("publisher")


class TestUsing(TestBase):
    def test_using(self):
        """Using should be passed through to each QuerySet."""
        with self.assertNumQueries(2):
            titles = [b.title for b in self.all.using("default")]
        self.assertEqual(titles, self.TITLES_BY_PK)


class TestSelectForUpdate(TestBase):
    def test_select_for_update(self):
        """select_for_update() locks the rows of every QuerySet."""
        with transaction.atomic():
            qss = self.all.select_for_update()
            for qs in qss.get_querysets():
                self.assertTrue(qs.query.select_for_update)
            with self.assertNumQueries(2):
                titles = [b.title for b in qss]
        self.assertEqual(titles, self.TITLES_BY_PK)

    def test_select_for_update_nowait(self):
        """nowait is passed through to every QuerySet."""
        qss = self.all.select_for_update(nowait=True)
        for qs in qss.get_querysets():
            self.assertTrue(qs.query.select_for_update_nowait)

    def test_select_for_update_skip_locked(self):
        """skip_locked is passed through to every QuerySet."""
        qss = self.all.select_for_update(skip_locked=True)
        for qs in qss.get_querysets():
            self.assertTrue(qs.query.select_for_update_skip_locked)

    def test_select_for_update_of(self):
        """of is passed through to every QuerySet."""
        qss = self.all.select_for_update(of=("self",))
        for qs in qss.get_querysets():
            self.assertEqual(qs.query.select_for_update_of, ("self",))

    @skipIf(django.VERSION < (6, 0), "no_key was added in Django 6.0.")
    def test_select_for_update_no_key(self):
        """no_key is passed through to every QuerySet."""
        qss = self.all.select_for_update(no_key=True)
        for qs in qss.get_querysets():
            self.assertTrue(qs.query.select_for_no_key_update)

    def test_select_for_update_nowait_and_skip_locked(self):
        """Django rejects combining nowait with skip_locked."""
        with self.assertRaises(ValueError):
            self.all.select_for_update(nowait=True, skip_locked=True)

    def test_select_for_update_empty(self):
        """An empty QuerySetSequence locks nothing."""
        with transaction.atomic():
            self.assertEqual(list(self.empty.select_for_update()), [])


class TestDistinct(TestBase):
    def test_distinct(self):
        """
        Distinct gets applied to each QuerySet, but not the overall QuerySetSequence.
        """
        # Create another publisher and add an existing book to it.
        publisher = Publisher.objects.create(name="Bigger Books")
        book = Book.objects.get(title="Biography")
        book.publishers.add(publisher)

        # Make a QuerySetSequence that would include non-distinct items.
        big_books = Book.objects.filter(publishers__name__startswith="Big")
        qss = QuerySetSequence(
            big_books, Article.objects.filter(publisher__name__startswith="Big")
        )

        # There should be more items than unique items.
        titles = [b.title for b in qss]
        self.assertGreater(len(titles), len(set(titles)))

        with self.assertNumQueries(0):
            qss = qss.distinct()

        # After calling distinct there should not be duplicated entries.
        titles = [b.title for b in qss]
        self.assertEqual(len(titles), len(set(titles)))

    def test_multiple_querysets_same_model(self):
        """
        Calling distinct on a QuerySetSequence made up of multiple QuerySet instances
        of the same model is not supported.
        """
        qss = QuerySetSequence(Book.objects.all(), Book.objects.all())
        with self.assertRaises(NotImplementedError):
            qss.distinct()


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

    def test_filter_args(self):
        """
        Ensure that filter() properly filters the children QuerySets, even when
        being passed args.
        """
        # Filter to just Bob's work.
        with self.assertNumQueries(0):
            bob_qss = self.all.filter(Q(author=self.bob))
        with self.assertNumQueries(2):
            self.assertEqual(bob_qss.count(), 3)

    def test_empty(self):
        """
        Ensure that filter() works when it results in an empty QuerySet.
        """
        # Filter to nothing.
        with self.assertNumQueries(0):
            qss = self.all.filter(title="")
        self.assertIsInstance(qss, QuerySetSequence)
        with self.assertNumQueries(2):
            self.assertEqual(qss.count(), 0)

        # This should not throw an exception.
        data = list(qss)
        self.assertEqual(len(data), 0)

    def _get_qss(self):
        """Returns a QuerySetSequence with 3 QuerySets."""
        return QuerySetSequence(
            Book.objects.all(), Article.objects.all(), BlogPost.objects.all()
        )

    def test_queryset(self):
        """Test filtering the QuerySets by exact lookups."""
        for key in ["#", "#__exact", "#__iexact"]:
            with self.assertNumQueries(0):
                qss = self._get_qss().filter(**{key: 1})

            with self.assertNumQueries(1):
                data = [it.title for it in qss]
            expected = [
                # Just the Articles.
                "Django Rocks",
                "Alice in Django-land",
                "Some Article",
            ]
            self.assertEqual(data, expected)

    def test_queryset_gt(self):
        """Test filtering the QuerySets by > lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{"#__gt": 0})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            # The Articles and BlogPosts.
            "Django Rocks",
            "Alice in Django-land",
            "Some Article",
            "Post",
        ]
        self.assertEqual(data, expected)

        # Additionally this should cast a string input to an int.
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{"#__gt": "0"})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, expected)

    def test_queryset_gte(self):
        """Test filtering the QuerySets by >= lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{"#__gte": 1})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            # The Articles and BlogPosts.
            "Django Rocks",
            "Alice in Django-land",
            "Some Article",
            "Post",
        ]
        self.assertEqual(data, expected)

    def test_queryset_lt(self):
        """Test filtering the QuerySets by < lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{"#__lt": 2})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        # The Books and Articles are returned.
        self.assertEqual(data, self.TITLES_BY_PK)

    def test_queryset_lte(self):
        """Test filtering the QuerySets by <= lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{"#__lte": 1})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        # The Books and Articles.
        self.assertEqual(data, self.TITLES_BY_PK)

    def test_queryset_in(self):
        """Filter the QuerySets with the in lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{"#__in": [1]})

        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        expected = [
            # Just the Articles.
            "Django Rocks",
            "Alice in Django-land",
            "Some Article",
        ]
        self.assertEqual(data, expected)

    def test_queryset_str(self):
        """Try filtering the QuerySets by various string lookups."""
        for key in [
            "#__contains",
            "#__icontains",
            "#__startswith",
            "#__istartswith",
            "#__endswith",
            "#__iendswith",
        ]:
            with self.assertNumQueries(0):
                qss = self._get_qss().filter(**{key: 1})

            with self.assertNumQueries(1):
                data = [it.title for it in qss]
            expected = [
                # Just the Articles.
                "Django Rocks",
                "Alice in Django-land",
                "Some Article",
            ]
            self.assertEqual(data, expected)

    def test_queryset_range(self):
        """Try filtering the QuerySets by the range lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{"#__range": [1, 2]})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            # The Articles and BlogPosts.
            "Django Rocks",
            "Alice in Django-land",
            "Some Article",
            "Post",
        ]
        self.assertEqual(data, expected)

    def test_queryset_unsupported(self):
        """Try filtering the QuerySets by a lookup that doesn't make sense."""
        with self.assertRaises(ValueError):
            self._get_qss().filter(**{"#__year": 1})

    def test_queryset_multiple(self):
        """
        When using multiple parameters to filter they get ANDed together. Ensure
        this works when filtering by QuerySet.
        """
        with self.assertNumQueries(0):
            qss = self._get_qss().filter(**{"#__gt": 0, "title__gt": "Django Rocks"})

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            # Some of the Articles and the BlogPosts.
            "Some Article",
            "Post",
        ]
        self.assertEqual(data, expected)

        # This would only look at Articles and BlogPosts, but neither of those
        # have a title > "Some Article."
        qss = self._get_qss().filter(**{"#__gt": 0, "title__gt": "Some Article"})

        # Only the articles are here because it's the second queryset.
        data = [it.title for it in qss]
        self.assertEqual(data, [])

    def test_filter_empty(self):
        """Calling filter on an empty QuerySetSequence doesn't error."""
        self.empty.filter(title="")


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
        return QuerySetSequence(
            Book.objects.all(), Article.objects.all(), BlogPost.objects.all()
        )

    def test_queryset(self):
        """Test excluding the QuerySets by exact lookups."""
        for key in ["#", "#__exact", "#__iexact"]:
            with self.assertNumQueries(0):
                qss = self._get_qss().exclude(**{key: 0})

            # The articles and blogposts are here because the first QuerySet is
            # removed.
            with self.assertNumQueries(2):
                data = [it.title for it in qss]
            expected = [
                # The Articles and BlogPosts.
                "Django Rocks",
                "Alice in Django-land",
                "Some Article",
                "Post",
            ]
            self.assertEqual(data, expected)

    def test_queryset_gt(self):
        """Test excluding the QuerySets by > lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{"#__gt": 1})

        # The books and articles are here.
        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        # The Books and Articles.
        self.assertEqual(data, self.TITLES_BY_PK)

    def test_queryset_gte(self):
        """Test excluding the QuerySets by >= lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{"#__gte": 1})

        # Only the blogposts are here because it's the last queryset.
        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        expected = [
            # Just the Books.
            "Fiction",
            "Biography",
        ]
        self.assertEqual(data, expected)

    def test_queryset_lt(self):
        """Test excluding the QuerySets by < lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{"#__lt": 1})

        # The articles and blogposts are here.
        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            # The Articles and BlogPosts.
            "Django Rocks",
            "Alice in Django-land",
            "Some Article",
            "Post",
        ]
        self.assertEqual(data, expected)

    def test_queryset_lte(self):
        """Test excluding the QuerySets by <= lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{"#__lte": 1})

        # Only the blogposts are here because it's the last queryset.
        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        expected = [
            # The BlogPosts.
            "Post",
        ]
        self.assertEqual(data, expected)

    def test_queryset_in(self):
        """exclude the QuerySets with the in lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{"#__in": [0, 2]})

        # Only the articles are here because it's the second queryset.
        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        expected = [
            # The Articles.
            "Django Rocks",
            "Alice in Django-land",
            "Some Article",
        ]
        self.assertEqual(data, expected)

    def test_queryset_str(self):
        """Try excluding the QuerySets by various string lookups."""
        for key in [
            "#__contains",
            "#__icontains",
            "#__startswith",
            "#__istartswith",
            "#__endswith",
            "#__iendswith",
        ]:
            with self.assertNumQueries(0):
                qss = self._get_qss().exclude(**{key: 1})

            # The books and blogposts are here.
            with self.assertNumQueries(2):
                data = [it.title for it in qss]
            expected = [
                # The Books and BlogPosts.
                "Fiction",
                "Biography",
                "Post",
            ]
            self.assertEqual(data, expected)

    def test_queryset_range(self):
        """Try excluding the QuerySets by the range lookup."""
        with self.assertNumQueries(0):
            qss = self._get_qss().exclude(**{"#__range": [1, 2]})

        # Only the books are here as it is the first queryset.
        with self.assertNumQueries(1):
            data = [it.title for it in qss]
        expected = [
            # Just the Articles.
            "Fiction",
            "Biography",
        ]
        self.assertEqual(data, expected)

    def test_queryset_unsupported(self):
        """Try excluding the QuerySets by a lookup that doesn't make sense."""
        with self.assertRaises(ValueError):
            self._get_qss().exclude(**{"#__year": 1})

    def test_exclude_empty(self):
        """Calling exclude on an empty QuerySetSequence doesn't error."""
        self.empty.exclude(title="")


class TestExtraAnnotate(TestBase):
    def test_extra(self):
        """Calling extra() gets applied to each QuerySet."""
        # Filter to just Bob's work.
        with self.assertNumQueries(0):
            bob_qss = self.all.extra(where=[f"author_id = '{self.bob.id}'"])
        with self.assertNumQueries(2):
            self.assertEqual(bob_qss.count(), 3)

    def test_annotate(self):
        """Annotating should get applied to each QuerySet."""
        qss = QuerySetSequence(
            Publisher.objects.all(), PeriodicalPublisher.objects.all()
        )
        qss = qss.annotate(published_count=Count("published")).order_by(
            "published_count"
        )

        # Each Published gets the count of things in it added.
        with self.assertNumQueries(2):
            data = [it.published_count for it in qss]
        self.assertEqual(data, [0, 2, 3])

    def test_aggregate(self):
        """aggregate() combines values across all QuerySets (Count sums)."""
        # Count sums across all QuerySets: 2 Books + 3 Articles = 5.
        self.assertEqual(self.all.aggregate(total=Count("pk")), {"total": 5})

    def test_aggregate_args(self):
        """aggregate() combines values across all QuerySets (Count sums)."""
        # Count sums across all QuerySets: 2 Books + 3 Articles = 5.
        self.assertEqual(self.all.aggregate(Count("pk")), {"pk__count": 5})

    def test_aggregate_args_kwargs(self):
        """aggregate() combines values across all QuerySets (Count sums)."""
        qs = QuerySetSequence(Book.objects.all(), Book.objects.all())
        self.assertEqual(
            qs.aggregate(Count("pk"), total=Sum("pages")), {"pk__count": 4, "total": 60}
        )

    def test_aggregate_empty(self):
        """aggregate() over an empty QuerySetSequence returns an empty dictionary."""
        self.assertEqual(self.empty.aggregate(total=Count("pk")), {})

    def test_aggregate_sum_same_model(self):
        """Sum combines across QuerySets of the same model."""
        # Two Book QuerySets, each with 2 books having pages=10 and pages=20.
        # Combined sum = (10 + 20) + (10 + 20) = 60.
        qs = QuerySetSequence(Book.objects.all(), Book.objects.all())
        self.assertEqual(qs.aggregate(total=Sum("pages")), {"total": 60})

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aaggregate(self):
        """aaggregate() combines values across all QuerySets (Count sums)."""
        self.assertEqual(await self.all.aaggregate(total=Count("pk")), {"total": 5})

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aaggregate_empty(self):
        """aaggregate() over an empty QuerySetSequence returns an empty dictionary."""
        self.assertEqual(await self.empty.aaggregate(total=Count("pk")), {})

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aaggregate_sum_same_model(self):
        """aaggregate() Sum combines across same-model QuerySets."""
        qs = QuerySetSequence(Book.objects.all(), Book.objects.all())
        self.assertEqual(await qs.aaggregate(total=Sum("pages")), {"total": 60})

    def test_aggregate_min_max_cross_model(self):
        """Min/Max combine across different models sharing the field."""
        # release exists on both Book and Article; min is earliest article (1979-01-01),
        # max is latest book (2002-12-24).
        qs = QuerySetSequence(Book.objects.all(), Article.objects.all())
        result = qs.aggregate(min_release=Min("release"), max_release=Max("release"))
        self.assertEqual(result["min_release"].year, 1979)
        self.assertEqual(result["max_release"].year, 2002)

    def test_aggregate_avg_unsupported(self):
        """aggregate() raises NotImplementedError for Avg."""
        with self.assertRaises(NotImplementedError):
            self.all.aggregate(average=Avg("release"))

    def test_aggregate_stddev_unsupported(self):
        """aggregate() raises NotImplementedError for StdDev."""
        with self.assertRaises(NotImplementedError):
            self.all.aggregate(stddev=StdDev("release"))

    def test_aggregate_variance_unsupported(self):
        """aggregate() raises NotImplementedError for Variance."""
        with self.assertRaises(NotImplementedError):
            self.all.aggregate(variance=Variance("release"))

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aaggregate_avg_unsupported(self):
        """aaggregate() raises NotImplementedError for Avg."""
        with self.assertRaises(NotImplementedError):
            await self.all.aaggregate(average=Avg("release"))

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aaggregate_stddev_unsupported(self):
        """aaggregate() raises NotImplementedError for StdDev."""
        with self.assertRaises(NotImplementedError):
            await self.all.aaggregate(stddev=StdDev("release"))

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aaggregate_variance_unsupported(self):
        """aaggregate() raises NotImplementedError for Variance."""
        with self.assertRaises(NotImplementedError):
            await self.all.aaggregate(variance=Variance("release"))


class TestOrderBy(TestBase):
    def test_order_by(self):
        """Ensure that order_by() propagates to QuerySets and iteration."""
        # Order by author and ensure it takes.
        with self.assertNumQueries(0):
            qss = self.all.order_by("title")

        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, sorted(self.TITLES_BY_PK))

    def test_order_by_nulls(self):
        """Test ordering by none values."""
        # Set the first item of each QuerySet to not have a release date.
        for qs in self.all.get_querysets():
            instance = qs.first()
            instance.release = None
            instance.save()

        # Check the nulls are properly ordered.
        with self.assertNumQueries(0):
            qss = self.all.order_by("release")

        with self.assertNumQueries(2):
            data = [(it.title, it.release is None) for it in qss]
        if connection.features.nulls_order_largest:
            expected = [
                ("Some Article", False),
                ("Alice in Django-land", False),
                ("Biography", False),
                ("Fiction", True),
                ("Django Rocks", True),
            ]
        else:
            expected = [
                ("Fiction", True),
                ("Django Rocks", True),
                ("Some Article", False),
                ("Alice in Django-land", False),
                ("Biography", False),
            ]
        self.assertEqual(data, expected)

        # Check ordering by reverse (fallback to the opposite QuerySet order to
        # make it match to reverse the expected lists above).
        with self.assertNumQueries(0):
            qss = self.all.order_by("-release", "-#")

        with self.assertNumQueries(2):
            data = [(it.title, it.release is None) for it in qss]
        self.assertEqual(data, list(reversed(expected)))

    def test_order_by_non_existent_field(self):
        """Ordering by a non-existent field raises an exception upon evaluation."""
        with self.assertRaises(FieldError):
            with self.assertNumQueries(0):
                self.all.order_by("pages")

    def test_order_by_multi(self):
        """Test ordering by multiple fields."""
        # Add another object with the same title, but a later release date.
        Book.objects.create(
            title="Fiction", author=self.alice, pages=1, release=date(2018, 10, 3)
        )

        with self.assertNumQueries(0):
            qss = self.all.order_by("title", "-release")

        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        expected = [
            "Alice in Django-land",
            "Biography",
            "Django Rocks",
            "Fiction",
            "Fiction",
            "Some Article",
        ]
        self.assertEqual(data, expected)

    def test_order_by_multi_2(self):
        """Test ordering by multiple fields, where # is not first."""
        # Add another object with the same title, but in a different QuerySet.
        Article.objects.create(
            title="Fiction",
            author=self.alice,
            publisher=self.mad_magazine,
            release=date(2018, 10, 3),
        )

        with self.assertNumQueries(0):
            qss = self.all.order_by("title", "-#")

        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = [(it.title, it.__class__.__name__) for it in qss]
        expected = [
            ("Alice in Django-land", "Article"),
            ("Biography", "Book"),
            ("Django Rocks", "Article"),
            ("Fiction", "Article"),
            ("Fiction", "Book"),
            ("Some Article", "Article"),
        ]
        self.assertEqual(data, expected)

    def test_order_by_relation(self):
        """
        Apply order_by() with a field that is a relation to another model's id.
        """
        # Order by author and ensure it takes.
        with self.assertNumQueries(0):
            qss = self.all.order_by("author_id")

        # The first two should be Alice, followed by three from Bob.
        with self.assertNumQueries(2):
            for expected, element in zip([self.alice.id] * 2 + [self.bob.id] * 3, qss):
                self.assertEqual(element.author_id, expected)

    def test_order_by_relation_pk(self):
        """
        Apply order_by() with a field that returns a model without a default
        ordering (i.e. using the pk).
        """
        # Order by author and ensure it takes.
        with self.assertNumQueries(0):
            qss = self.all.order_by("author")

        # Ensure that the test has any hope of passing.
        self.assertLess(self.alice.pk, self.bob.pk)

        # The first three should be from Mad Magazine, followed by three from
        # Big Books.
        # Note that the QuerySetSequence itself needs the publisher objects to
        # compare them, so they all get pulled in.
        with self.assertNumQueries(2 + 5):
            self.assertEqual(
                [self.alice.id] * 2 + [self.bob.id] * 3,
                [b.author.id for b in qss],
            )

    def test_order_by_relation_with_ordering(self):
        """
        Apply order_by() with a field that returns a model with a default
        ordering.
        """
        # Order by author and ensure it takes.
        with self.assertNumQueries(0):
            qss = self.all.order_by("author")

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
            qss = all.order_by("publisher")

        with self.assertRaises(FieldError):
            list(qss)

    def test_order_by_relation_field(self):
        """Apply order_by() with a field through a model relationship."""
        # Order by author name and ensure it takes.
        with self.assertNumQueries(0):
            qss = self.all.order_by("author__name")

        # The first two should be Alice, followed by three from Bob.
        # Note that the QuerySetSequence itself needs the author objects to
        # compare them, so they all get pulled in.
        with self.assertNumQueries(2 + 5):
            for expected, element in zip([self.alice.id] * 2 + [self.bob.id] * 3, qss):
                self.assertEqual(element.author.id, expected)

    def test_order_by_queryset(self):
        """Ensure we can order by QuerySet and then other fields."""
        # Order by title, but don't interleave each QuerySet.
        with self.assertNumQueries(0):
            qss = self.all.order_by("#", "title")

        # Ensure that _ordered_iterator isn't called.
        with patch(
            "queryset_sequence.BaseIterable._ordered_iterator",
            side_effect=AssertionError("_ordered_iterator should not be called"),
        ):
            # Check the titles are properly ordered.
            data = [it.title for it in qss]
            expected = [
                # First the Books, in order.
                "Biography",
                "Fiction",
                # Then the Articles, in order.
                "Alice in Django-land",
                "Django Rocks",
                "Some Article",
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
            qss = self.all.order_by("-#", "title")

        # Ensure that _ordered_iterator isn't called.
        with patch(
            "queryset_sequence.BaseIterable._ordered_iterator",
            side_effect=AssertionError("_ordered_iterator should not be called"),
        ):
            # Check the titles are properly ordered.
            data = [it.title for it in qss]
            expected = [
                # The articles, in order.
                "Alice in Django-land",
                "Django Rocks",
                "Some Article",
                # Then the Books, in order.
                "Biography",
                "Fiction",
            ]
            self.assertEqual(data, expected)

    def test_empty(self):
        """Calling order_by on an empty QuerySetSequence doesn't error."""
        self.empty.order_by("author")


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
            qss = self.all.order_by("title").reverse()

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data, sorted(self.TITLES_BY_PK, reverse=True))

    def test_reverse_twice_ordered(self):
        """Calling reverse() twice is negated, but then order by title."""
        with self.assertNumQueries(0):
            qss = self.all.reverse().order_by("title").reverse()

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
        self.assertEqual(result.title, "Fiction")
        self.assertIsInstance(result, Book)

    def test_one_QuerySet(self):
        """Test slicing only from one QuerySet."""
        with self.assertNumQueries(0):
            qss = self.all[0:2]

        # 2 counts + evaluating one QuerySet.
        with self.assertNumQueries(3):
            data = [it.title for it in qss]
        self.assertEqual(["Fiction", "Biography"], data)

    def test_cast_list(self):
        """Test slicing and casting to a list."""
        with self.assertNumQueries(0):
            qss = self.all[0:2]

        # 2 counts + evaluating one QuerySet.
        with self.assertNumQueries(3):
            result = list(qss)
            data = [it.title for it in result]
        self.assertEqual(["Fiction", "Biography"], data)

    def test_multiple_QuerySets(self):
        """Test slicing across elements from multiple QuerySets."""
        # 2 counts + 2 evaluations.
        with self.assertNumQueries(0):
            qss = self.all[1:3]

        # 2 counts + evaluating two QuerySets.
        with self.assertNumQueries(4):
            data = [it.title for it in qss]
        self.assertEqual(["Biography", "Django Rocks"], data)

    def test_multiple_slices(self):
        """Test multiple slices taken."""
        with self.assertNumQueries(0):
            result = self.all[1:3]
        self.assertIsInstance(result, QuerySetSequence)
        # Evaluate the QuerySet.
        with self.assertNumQueries(3):
            article = result[1]
        self.assertEqual(article.title, "Django Rocks")

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
        self.assertEqual(data, ["Django Rocks"])

    def test_step(self):
        """Test behavior when a step is provided to the slice."""
        with self.assertNumQueries(4):
            qss = self.all[0:4:2]
            data = [it.title for it in qss]
        self.assertIsInstance(qss, list)

        self.assertEqual(["Fiction", "Django Rocks"], data)

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
            qss = self.all.order_by("title")[1:3]
        self.assertIsInstance(qss, QuerySetSequence)

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(data[0], "Biography")
        self.assertEqual(data[1], "Django Rocks")

    def test_open_slice(self):
        """Test slicing without an end."""
        qss = QuerySetSequence(Article.objects.all())[1:]

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(["Alice in Django-land", "Some Article"], data)

    def test_closed_slice_single_qs(self):
        """Test slicing if the start and end are within the same QuerySet."""
        Article.objects.create(
            title="Another Article",
            author=self.bob,
            publisher=self.mad_magazine,
            release=date(2018, 10, 3),
        )

        qss = QuerySetSequence(Article.objects.all())[1:3]

        with self.assertNumQueries(2):
            data = [it.title for it in qss]
        self.assertEqual(["Alice in Django-land", "Some Article"], data)

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
            book = self.all.get(title="Biography")
        self.assertEqual(book.title, "Biography")
        self.assertIsInstance(book, Book)

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aget(self):
        """
        Ensure that aget() returns the expected element or raises DoesNotExist.
        """
        # Get a particular item.
        book = await self.all.aget(title="Biography")
        self.assertEqual(book.title, "Biography")
        self.assertIsInstance(book, Book)

    def test_not_found(self):
        # An exception is raised if get() is called and nothing is found.
        with self.assertNumQueries(2):
            with self.assertRaises(ObjectDoesNotExist):
                self.all.get(title="")

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aget_not_found(self):
        with self.assertRaises(ObjectDoesNotExist):
            await self.all.aget(title="")

    def test_multi_found(self):
        """Test multiple found in the same QuerySet."""
        # ...or if get() is called and multiple objects are found.
        with self.assertNumQueries(1):
            with self.assertRaises(MultipleObjectsReturned):
                self.all.get(author=self.bob)

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aget_multi_found(self):
        """Test multiple found in the same QuerySet."""
        # ...or if aget() is called and multiple objects are found.
        with self.assertRaises(MultipleObjectsReturned):
            await self.all.aget(author=self.bob)

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    def test_multi_found_separate_querysets(self):
        """Test one found in each QuerySet."""
        # ...or if get() is called and multiple objects are found.
        with self.assertNumQueries(2):
            with self.assertRaises(MultipleObjectsReturned):
                self.all.get(title__contains="A")

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aget_multi_found_separate_querysets(self):
        """Test one found in each QuerySet."""
        # ...or if aget() is called and multiple objects are found.
        with self.assertRaises(MultipleObjectsReturned):
            await self.all.aget(title__contains="A")

    def test_related_model(self):
        qss = QuerySetSequence(Article.objects.all(), BlogPost.objects.all())
        with self.assertNumQueries(2):
            post = qss.get(publisher__name="Wacky Website")
        self.assertEqual(post.title, "Post")
        self.assertIsInstance(post, BlogPost)

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aget_related_model(self):
        qss = QuerySetSequence(Article.objects.all(), BlogPost.objects.all())
        post = await qss.aget(publisher__name="Wacky Website")
        self.assertEqual(post.title, "Post")
        self.assertIsInstance(post, BlogPost)

    def test_queryset_lookup(self):
        """Test using the special QuerySet lookup."""
        with self.assertNumQueries(1):
            article = self.all.get(**{"#": 1, "author": self.bob})
        self.assertEqual(article.title, "Some Article")
        self.assertIsInstance(article, Article)

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aget_queryset_lookup(self):
        """Test using the special QuerySet lookup."""
        article = await self.all.aget(**{"#": 1, "author": self.bob})
        self.assertEqual(article.title, "Some Article")
        self.assertIsInstance(article, Article)

    def test_empty(self):
        """Calling get on an empty QuerySetSequence raises ObjectDoesNotExist."""
        with self.assertRaises(ObjectDoesNotExist):
            self.empty.get(pk=1)

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aget_empty(self):
        """Calling get on an empty QuerySetSequence raises ObjectDoesNotExist."""
        with self.assertRaises(ObjectDoesNotExist):
            await self.empty.get(pk=1)


class TestBoolean(TestBase):
    """Tests related to casting the QuerySetSequence to a boolean."""

    def test_exists(self):
        """Ensure that it casts to True if the item is found."""
        with self.assertNumQueries(2):
            self.assertTrue(self.all.filter(title="Biography"))

    def test_exists_second(self):
        """
        Ensure that it casts to True if the item is found in a subsequent QuerySet.
        """
        with self.assertNumQueries(2):
            self.assertTrue(self.all.filter(title="Alice in Django-land"))

    def test_not_found(self):
        """Ensure that exists() returns False if the item is not found."""
        with self.assertNumQueries(2):
            self.assertFalse(self.all.filter(title=""))

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
            earliest = self.all.earliest("release")
        self.assertEqual(earliest.title, "Some Article")

    def test_latest(self):
        """The latest release overall should be returned."""
        with self.assertNumQueries(2):
            latest = self.all.latest("release")
        self.assertEqual(latest.title, "Biography")

    def test_earliest_reverse(self):
        """The earliest release overall reversed is the latest."""
        with self.assertNumQueries(2):
            earliest = self.all.earliest("-release")
        self.assertEqual(earliest.title, "Biography")

    def test_latest_reverse(self):
        """The latest release overall reversed is the earliest."""
        with self.assertNumQueries(2):
            latest = self.all.latest("-release")
        self.assertEqual(latest.title, "Some Article")

    def test_earliest_get_latest_by(self):
        """Not providing fields causes the get_latest_by field to be used."""
        with self.assertNumQueries(2):
            latest = self.all.earliest()
        self.assertEqual(latest.title, "Some Article")

    def test_earliest_get_latest_by_error(self):
        """When get_latest_by is used, they must all be the same."""
        with self.assertRaises(ValueError):
            QuerySetSequence(Book.objects.all(), BlogPost.objects.all()).earliest()

    def test_latest_get_latest_by(self):
        """Not providing fields causes the get_latest_by field to be used."""
        with self.assertNumQueries(2):
            latest = self.all.latest()
        self.assertEqual(latest.title, "Biography")

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

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aearliest(self):
        """The earliest release overall should be returned."""
        earliest = await self.all.aearliest("release")
        self.assertEqual(earliest.title, "Some Article")

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_alatest(self):
        """The latest release overall should be returned."""
        latest = await self.all.alatest("release")
        self.assertEqual(latest.title, "Biography")

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aearliest_reverse(self):
        """The earliest release overall reversed is the latest."""
        earliest = await self.all.aearliest("-release")
        self.assertEqual(earliest.title, "Biography")

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_alatest_reverse(self):
        """The latest release overall reversed is the earliest."""
        latest = await self.all.alatest("-release")
        self.assertEqual(latest.title, "Some Article")

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aearliest_get_latest_by(self):
        """Not providing fields causes the get_latest_by field to be used."""
        earliest = await self.all.aearliest()
        self.assertEqual(earliest.title, "Some Article")

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_alatest_get_latest_by(self):
        """Not providing fields causes the get_latest_by field to be used."""
        latest = await self.all.alatest()
        self.assertEqual(latest.title, "Biography")

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aearliest_empty(self):
        """An empty QuerySetSequence raises a ValueError."""
        with self.assertRaises(ValueError):
            await self.empty.aearliest()

        with self.assertRaises(ValueError):
            await self.empty.alatest()


class TestFirstLast(TestBase):
    def test_first_unordered(self):
        """Should return the first element of the first QuerySet."""
        with self.assertNumQueries(1):
            self.assertEqual(self.all.first().title, "Fiction")

    def test_last_unordered(self):
        """Should return the last element of the last QuerySet."""
        with self.assertNumQueries(1):
            self.assertEqual(self.all.last().title, "Some Article")

    def test_empty(self):
        """Empty QuerySetSequence should work."""
        self.assertIsNone(self.empty.first())
        self.assertIsNone(self.empty.last())

    def test_first_ordered(self):
        """When ordering, the items of each QuerySet must be compared."""
        # Order by author and ensure it takes.
        with self.assertNumQueries(2):
            self.assertEqual(
                self.all.order_by("title").first().title, "Alice in Django-land"
            )

        with self.assertNumQueries(2):
            self.assertEqual(self.all.order_by("-title").first().title, "Some Article")

    def test_last_ordered(self):
        """When ordering, the items of each QuerySet must be compared."""
        # Order by author and ensure it takes.
        with self.assertNumQueries(2):
            self.assertEqual(
                self.all.order_by("-title").last().title, "Alice in Django-land"
            )

        with self.assertNumQueries(2):
            self.assertEqual(self.all.order_by("title").last().title, "Some Article")

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_afirst_unordered(self):
        """Should return the first element of the first QuerySet."""
        self.assertEqual((await self.all.afirst()).title, "Fiction")

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_alast_unordered(self):
        """Should return the last element of the last QuerySet."""
        self.assertEqual((await self.all.alast()).title, "Some Article")

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_afirst_empty(self):
        """Empty QuerySetSequence should work."""
        self.assertIsNone(await self.empty.afirst())
        self.assertIsNone(await self.empty.alast())

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_afirst_ordered(self):
        """When ordering, the items of each QuerySet must be compared."""
        self.assertEqual(
            (await self.all.order_by("title").afirst()).title, "Alice in Django-land"
        )

        self.assertEqual(
            (await self.all.order_by("-title").afirst()).title, "Some Article"
        )

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_alast_ordered(self):
        """When ordering, the items of each QuerySet must be compared."""
        self.assertEqual(
            (await self.all.order_by("-title").alast()).title, "Alice in Django-land"
        )

        self.assertEqual(
            (await self.all.order_by("title").alast()).title, "Some Article"
        )


class TestExists(TestBase):
    def test_exists(self):
        """
        Ensure that exists() returns True if the item is found in the first QuerySet.
        """
        with self.assertNumQueries(1):
            self.assertTrue(self.all.filter(title="Biography").exists())

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aexists(self):
        """
        Ensure that aexists() returns True if the item is found in the first QuerySet.
        """
        self.assertTrue(await self.all.filter(title="Biography").aexists())

    def test_exists_second(self):
        """
        Ensure that exists() returns True if the item is found in a subsequent QuerySet.
        """
        with self.assertNumQueries(2):
            self.assertTrue(self.all.filter(title="Alice in Django-land").exists())

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aexists_second(self):
        """
        Ensure that aexists() returns True if the item is found in a subsequent
        QuerySet.
        """
        self.assertTrue(await self.all.filter(title="Alice in Django-land").aexists())

    def test_not_found(self):
        """Ensure that exists() returns False if the item is not found."""
        with self.assertNumQueries(2):
            self.assertFalse(self.all.filter(title="").exists())

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aexists_not_found(self):
        """Ensure that aexists() returns False if the item is not found."""
        self.assertFalse(await self.all.filter(title="").aexists())

    def test_multi_found(self):
        """Ensure that exists() returns True if multiple items are found."""
        with self.assertNumQueries(1):
            self.assertTrue(self.all.filter(author=self.bob).exists())

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aexists_multi_found(self):
        """Ensure that aexists() returns True if multiple items are found."""
        self.assertTrue(await self.all.filter(author=self.bob).aexists())

    def test_empty(self):
        """An empty QuerySetSequence should return False."""
        self.assertFalse(self.empty.exists())

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aexists_empty(self):
        """An empty QuerySetSequence should return False."""
        self.assertFalse(await self.empty.aexists())


@skipIf(django.VERSION < (4, 0), "Not supported in Django < 4.0.")
class TestContains(TestBase):
    def test_contains(self):
        """
        Ensure that contains() returns True if the item is found in the first QuerySet.
        """
        obj = self.all.get_querysets()[0].first()
        with self.assertNumQueries(1):
            self.assertTrue(self.all.contains(obj))

    def test_contains_second(self):
        """
        Ensure that contains() returns True if the item is found in a subsequent
        QuerySet.
        """
        obj = self.all.get_querysets()[1].first()
        with self.assertNumQueries(1):
            self.assertTrue(self.all.contains(obj))

    def test_not_found(self):
        """Ensure that contains() returns False if the item is not found."""
        obj = self.all.get_querysets()[0].first()
        with self.assertNumQueries(1):
            self.assertFalse(self.all.exclude(pk=obj.pk).contains(obj))

    def test_wrong_type(self):
        """Queries should not occur if the value is the wrong type."""
        obj = self.all.get_querysets()[0].first().author
        with self.assertNumQueries(0):
            self.assertFalse(self.all.contains(obj))

    def test_empty(self):
        """An empty QuerySetSequence should return False."""
        obj = self.all.get_querysets()[0].first()
        self.assertFalse(self.empty.contains(obj))

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_acontains(self):
        """
        Ensure that acontains() returns True if the item is found in the first QuerySet.
        """
        obj = await self.all.get_querysets()[0].afirst()
        self.assertTrue(await self.all.acontains(obj))

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_acontains_second(self):
        """
        Ensure that acontains() returns True if the item is found in a subsequent
        QuerySet.
        """
        obj = await self.all.get_querysets()[1].afirst()
        self.assertTrue(await self.all.acontains(obj))

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_acontains_not_found(self):
        """Ensure that acontains() returns False if the item is not found."""
        obj = await self.all.get_querysets()[0].afirst()
        self.assertFalse(await self.all.exclude(pk=obj.pk).acontains(obj))

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_acontains_wrong_type(self):
        """Queries should not occur if the value is the wrong type."""
        obj = await self.all.get_querysets()[0].afirst()
        author = await sync_to_async(lambda: obj.author)()
        self.assertFalse(await self.all.acontains(author))

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_acontains_empty(self):
        """An empty QuerySetSequence should return False."""
        obj = await self.all.get_querysets()[0].afirst()
        self.assertFalse(await self.empty.acontains(obj))


class TestUpdate(TestBase):
    def test_update(self):
        """Update should apply across all QuerySets."""
        # The queries are: creating a save point, the two updates, releasing the
        # save point.
        with self.assertNumQueries(4):
            result = self.all.update(title="A New Title")
        self.assertEqual(result, 5)

        with self.assertNumQueries(2):
            data = [it.title for it in self.all]
        self.assertEqual(data, ["A New Title"] * 5)

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

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aupdate(self):
        """Update should apply across all QuerySets."""
        result = await self.all.aupdate(title="A New Title")
        self.assertEqual(result, 5)

        data = await sync_to_async(lambda: [it.title for it in self.all])()
        self.assertEqual(data, ["A New Title"] * 5)

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aupdate_error(self):
        """If an error occurs on one of the QuerySets, no changes should occur."""
        with self.assertRaises(FieldDoesNotExist):
            await self.all.aupdate(pages=8)

        # The page counts for the Book objects are unmodified.
        data = await sync_to_async(lambda: [it.pages for it in Book.objects.all()])()
        self.assertEqual(data, [10, 20])

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_aupdate_empty(self):
        """Calling update on an empty QuerySetSequence should work."""
        result = await self.empty.aupdate()
        self.assertEqual(result, 0)


class TestDelete(TestBase):
    def test_delete_all(self):
        """Ensure that delete() works properly."""
        # 4 queries is due to the models themselves and then the many-to-many
        # relationships.
        with self.assertNumQueries(4):
            result = self.all.delete()
        self.assertEqual(result[0], 7)
        self.assertEqual(
            result[1], {"tests.Article": 3, "tests.Book": 2, "tests.Book_publishers": 2}
        )

        with self.assertNumQueries(2):
            self.assertEqual(self.all.count(), 0)

    def test_delete_filter(self):
        """Ensure that delete() works properly when filtering."""
        with self.assertNumQueries(2):
            result = self.all.filter(author=self.alice).delete()
        self.assertEqual(result[0], 2)
        expected = {"tests.Article": 2}
        self.assertEqual(result[1], expected)

        with self.assertNumQueries(2):
            self.assertEqual(self.all.count(), 3)

    def test_empty(self):
        """Calling delete on an empty QuerySetSequence should work."""
        result = self.empty.delete()
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], {})

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_adelete_all(self):
        """Ensure that adelete() works properly."""
        result = await self.all.adelete()
        self.assertEqual(result[0], 7)
        self.assertEqual(
            result[1], {"tests.Article": 3, "tests.Book": 2, "tests.Book_publishers": 2}
        )

        self.assertEqual(await self.all.acount(), 0)

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_adelete_filter(self):
        """Ensure that adelete() works properly when filtering."""
        result = await self.all.filter(author=self.alice).adelete()
        self.assertEqual(result[0], 2)
        expected = {"tests.Article": 2}
        self.assertEqual(result[1], expected)

        self.assertEqual(await self.all.acount(), 3)

    @skipIf(django.VERSION < (4, 1), "Not supported in Django < 4.1.")
    async def test_adelete_empty(self):
        """Calling delete on an empty QuerySetSequence should work."""
        result = await self.empty.adelete()
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], {})


class TestExplain(TestBase):
    def test_supported(self):
        """Supported versions of Django support explain() and return a string."""
        with self.assertNumQueries(2):
            explanation = self.all.explain()
        # The output of explain is not guaranteed, so do some rough checks.
        self.assertEqual(len(explanation.split("\n")), 2)


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

    async def test_acreate(self):
        with self.assertRaises(ImplementedIn41):
            await self.all.acreate()

    def test_get_or_create(self):
        with self.assertRaises(NotImplementedError):
            self.all.get_or_create()

    async def test_aget_or_create(self):
        with self.assertRaises(ImplementedIn41):
            await self.all.aget_or_create()

    def test_update_or_create(self):
        with self.assertRaises(NotImplementedError):
            self.all.update_or_create()

    async def test_aupdate_or_create(self):
        with self.assertRaises(ImplementedIn41):
            await self.all.aupdate_or_create()

    def test_bulk_create(self):
        with self.assertRaises(NotImplementedError):
            self.all.bulk_create([])

    async def test_abulk_create(self):
        with self.assertRaises(ImplementedIn41):
            await self.all.abulk_create([])

    def test_bulk_update(self):
        with self.assertRaises(NotImplementedError):
            self.all.bulk_update([], [])

    async def test_abulk_update(self):
        with self.assertRaises(ImplementedIn41):
            await self.all.abulk_update([], [])

    def test_in_bulk(self):
        with self.assertRaises(NotImplementedError):
            self.all.in_bulk()

    async def test_ain_bulk(self):
        with self.assertRaises(ImplementedIn41):
            await self.all.ain_bulk()


class TestNotImplemented(TestCase):
    """The following methods have not been implemented in QuerySetSequence."""

    def setUp(self):
        self.all = QuerySetSequence()

    def test_union(self):
        with self.assertRaises(NotImplementedError):
            self.all.union()

    def test_intersection(self):
        with self.assertRaises(NotImplementedError):
            self.all.intersection()

    def test_difference(self):
        with self.assertRaises(NotImplementedError):
            self.all.difference()

    def test_raw(self):
        with self.assertRaises(NotImplementedError):
            self.all.raw("")

    @skipIf(django.VERSION >= (4, 1), "aget exists starting on Django 4.1.")
    async def test_aget(self):
        with self.assertRaises(AttributeError):
            await self.all.aget()

    @skipIf(django.VERSION >= (4, 1), "acount exists starting on Django 4.1.")
    async def test_acount(self):
        with self.assertRaises(AttributeError):
            await self.all.acount()

    async def test_aiterator(self):
        with self.assertRaises(ImplementedIn41):
            await self.all.aiterator()

    @skipIf(django.VERSION >= (4, 1), "alatest exists starting on Django 4.1.")
    async def test_alatest(self):
        with self.assertRaises(ImplementedIn41):
            await self.all.alatest()

    @skipIf(django.VERSION >= (4, 1), "aearliest exists starting on Django 4.1.")
    async def test_aearliest(self):
        with self.assertRaises(ImplementedIn41):
            await self.all.aearliest()

    @skipIf(django.VERSION >= (4, 1), "afirst exists starting on Django 4.1.")
    async def test_afirst(self):
        with self.assertRaises(ImplementedIn41):
            await self.all.afirst()

    @skipIf(django.VERSION >= (4, 1), "alast exists starting on Django 4.1.")
    async def test_alast(self):
        with self.assertRaises(ImplementedIn41):
            await self.all.alast()

    @skipIf(django.VERSION >= (4, 1), "aexists exists starting on Django 4.1.")
    async def test_aexists(self):
        with self.assertRaises(AttributeError):
            await self.all.aexists()

    @skipIf(django.VERSION >= (4, 1), "acontains exists starting on Django 4.1.")
    async def test_acontains(self):
        with self.assertRaises(AttributeError):
            await self.all.acontains()

    @skipIf(django.VERSION >= (4, 1), "aupdate exists starting on Django 4.1.")
    async def test_aupdate(self):
        with self.assertRaises(AttributeError):
            await self.all.aupdate()

    @skipIf(django.VERSION >= (4, 1), "adelete exists starting on Django 4.1.")
    async def test_adelete(self):
        with self.assertRaises(AttributeError):
            await self.all.adelete()

    @skipIf(django.VERSION >= (4, 1), "aexplain exists starting on Django 4.1.")
    async def test_aexplain(self):
        with self.assertRaises(AttributeError):
            await self.all.aexplain()

    @skipIf(django.VERSION >= (3, 2), "alias exists starting on Django 3.2.")
    def test_alias(self):
        with self.assertRaises(AttributeError):
            self.all.alias()

    @skipIf(django.VERSION >= (4, 0), "Contains exists starting on Django 4.0.")
    def test_contains(self):
        obj = 1
        self.all.contains(obj)

    @skipIf(django.VERSION >= (6, 1), "fetch_mode exists starting on Django 6.1.")
    def test_fetch_mode(self):
        with self.assertRaises(AttributeError):
            self.all.fetch_mode()

    @skipIf(django.VERSION >= (6, 1), "totally_ordered exists starting on Django 6.1.")
    def test_totally_ordered(self):
        with self.assertRaises(AttributeError):
            self.all.totally_ordered


@skipIf(django.VERSION < (6, 1), "fetch_mode requires Django 6.1+")
class TestFetchMode(TestBase):
    def test_fetch_mode(self):
        """fetch_mode() delegates to each underlying QuerySet."""
        qss = self.all.fetch_mode("FETCH_PEERS")
        self.assertIsInstance(qss, QuerySetSequence)
        self.assertEqual(len(qss.get_querysets()), 2)

    def test_empty(self):
        """fetch_mode() works on empty QuerySetSequence."""
        qss = self.empty.fetch_mode("FETCH_PEERS")
        self.assertIsInstance(qss, QuerySetSequence)
        self.assertEqual(len(qss.get_querysets()), 0)


@skipIf(django.VERSION < (6, 1), "totally_ordered requires Django 6.1+")
class TestTotallyOrdered(TestBase):
    def test_totally_ordered_false_when_unordered(self):
        """totally_ordered is False when no ordering is set."""
        self.assertFalse(self.all.totally_ordered)

    def test_totally_ordered_false_when_not_unique(self):
        """totally_ordered is False when ordering is not unique."""
        # Order by author (not unique)
        qss = self.all.order_by("author")
        self.assertTrue(qss.ordered)
        # Since author is not unique, totally_ordered should be False
        self.assertFalse(qss.totally_ordered)

    def test_totally_ordered_empty(self):
        """totally_ordered works on empty QuerySetSequence."""
        self.assertFalse(self.empty.totally_ordered)


class TestAlias(TestBase):
    @skipIf(django.VERSION < (3, 2), "alias() requires Django 3.2+")
    def test_alias(self):
        """alias() delegates to each underlying QuerySet."""
        qss = self.all.alias(entry_count=Count("pk"))
        self.assertIsInstance(qss, QuerySetSequence)

    @skipIf(django.VERSION < (3, 2), "alias() requires Django 3.2+")
    def test_alias_empty(self):
        """alias() works on empty QuerySetSequence."""
        qss = self.empty.alias(test=Count("pk"))
        self.assertIsInstance(qss, QuerySetSequence)
        self.assertEqual(len(qss.get_querysets()), 0)
