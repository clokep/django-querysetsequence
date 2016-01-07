from django.test import TestCase

from queryset_sequence import QuerySetSequence

from .models import Article, Author, Book

class TestQuerySetSequence(TestCase):
    def test_length(self):
        bob = Author.objects.create(name="Bob")

        book = Book.objects.create(title="Biography", author=bob)
        article = Article.objects.create(title="Some Article", author=bob)

        qss = QuerySetSequence(Book.objects.all(), Article.objects.all())

        self.assertEqual(qss.count(), 2)
        self.assertEqual(len(qss), 2)
