Django QuerySetSequence
#######################

The ``QuerySetSequence`` wrapper helps to deal with disparate ``QuerySet``
classes, while treating them as a single ``QuerySet``.

Supported Features
==================

* ``filter()`` / ``exclude()`` across fields common to all sub-``QuerySets``.
* ``order_by()`` fields common across all sub-``QuerySets``.
* ``len()`` / ``count()`` to get the total length across all ``QuerySets``.
* Slicing and indexing works as expected.
* ``QuerySetSequence`` is an iterable.
* ``QuerySets`` are evaluated as late as possible.

Known Issues
============

* Cannot handle ``order_by()`` when fields include other models (e.g.
  ``ForeignKeys``).
* The fully ``QuerySet`` API is not complete.

Installation
============

Install the package using pip.

.. code-block:: bash

    pip install --upgrade django-querysetsequence

Usage
=====

.. code-block:: python

    # Import QuerySetSequence
    from queryset_sequence import QuerySetSequence

    # Create QuerySets you want to chain.
    from .models import SomeModel, OtherModel

    # Chain them together.
    query = QuerySetSequence(SomeModel.objects.all(), OtherModel.objects.all())

    # Use query as if it were a QuerySet! E.g. in a ListView.


Example
=======

.. code-block:: python

    class Author(models.Model):
        name = models.CharField(max_length=50)

        class Meta:
            ordering = ['name']

        def __str__(self):
            return self.name


    class Article(models.Model):
        title = models.CharField(max_length=100)
        author = models.ForeignKey(Author)

        def __str__(self):
            return "%s by %s" % (self.title, self.author)


    class Book(models.Model):
        title = models.CharField(max_length=50)
        author = models.ForeignKey(Author)
        release = models.DateField(auto_now_add=True)

        def __str__(self):
            return "%s by %s" % (self.title, self.author)

    # Create some data.
    alice = Author.objects.create(name='Alice')
    article = Article.objects.create(title='Dancing with Django', author=alice)

    bob = Author.objects.create(name='Bob')
    article = Article.objects.create(title='Django-isms', author=bob)
    article = Book.objects.create(title='Biography', author=bob)

    # Create some QuerySets.
    books = Book.objects.all()
    articles = Article.objects.all()

    # Combine them into a single iterable.
    published_works = QuerySetSequence(books, articles)

    # Find Bob's titles.
    bob_works = published_works.filter(author=bob)
    # Still an iterable.
    print([w.title for w in bob_works])  # prints: ['Biography', 'Django-isms']

    # Alphabetize the QuerySet.
    published_works = published_works.order_by('title')
    print([w.title for w in published_works])  # prints ['Biography', 'Dancing with Django', 'Django-isms']

Attribution
===========

This is based on a few DjangoSnippets that had been going around:

* Originally from https://www.djangosnippets.org/snippets/1103/
* Modified version from https://djangosnippets.org/snippets/1253/
* Upgraded version from https://djangosnippets.org/snippets/1933/
* Updated version from `django-ko-demo from The Atlantic <https://github.com/theatlantic/django-ko-demo/blob/1a37c9ad9bcd68a40c35462fb819fff85a9533f7/apps/curation_nouveau/queryset_sequence.py>`_


Contribute
==========

* Check for open issues or open a fresh issue to start a discussion around a
  feature idea or a bug.
* Fork the repository on GitHub to start making your changes.
* Write a test which shows that the bug was fixed or that the feature works as
  expected.
* Send a pull request and bug the maintainer until it gets merged and published.
