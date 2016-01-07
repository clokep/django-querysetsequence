from django.test import TestCase

from queryset_sequence import QuerySetSequence

from .models import Article, Author, Book

class TestQuerySetSequence(TestCase):
    @classmethod
    def setUpClass(cls):
        """Set-up some data to be tested against."""
        alice = Author.objects.create(name="Alice")
        bob = Author.objects.create(name="Bob")

        # Alice wrote some articles.
        Article.objects.create(title="Django Rocks", author=alice)
        Article.objects.create(title="Alice in Django-land", author=alice)

        # Bob wrote a couple of books and an article.
        Book.objects.create(title="Fiction", author=bob)
        Book.objects.create(title="Biography", author=bob)
        Article.objects.create(title="Some Article", author=bob)

        # Save the authors for later.
        cls.alice = alice
        cls.bob = bob

    @classmethod
    def tearDownClass(cls):
        del cls.alice
        del cls.bob

        # Clear the database.
        Author.objects.all().delete()
        Article.objects.all().delete()
        Book.objects.all().delete()

    def test_length(self):
        qss = QuerySetSequence(Book.objects.filter(author=self.bob),
                               Article.objects.filter(author=self.bob))

        # The proper length should be returned via database queries.
        self.assertEqual(qss.count(), 3)
        self.assertIsNone(qss._result_cache)

        # Calling len() evaluates the QuerySet.
        self.assertEqual(len(qss), 3)
        self.assertIsNotNone(qss._result_cache)

        # Count should still work (and not hit the database).
        qss.query = None
        self.assertEqual(qss.count(), 3)

    def test_filter(self):
        qss = QuerySetSequence(Book.objects.all(), Article.objects.all())

        # Check that everything is in the current list.
        self.assertEqual(qss.count(), 5)

        # Now filter to just Bob's work.
        bob_qss = qss.filter(author=self.bob)
        self.assertEqual(bob_qss.count(), 3)
