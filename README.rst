Django QuerySetSequence
#######################

.. image:: https://travis-ci.org/percipient/django-querysetsequence.svg?branch=master
    :target: https://travis-ci.org/percipient/django-querysetsequence

The ``QuerySetSequence`` wrapper helps to deal with disparate ``QuerySet``
classes, while treating them as a single ``QuerySet``.

Supported Features
==================

Listed below are features of Django's |QuerySets|_ that ``QuerySetSequence``
implements. The behavior should match that of ``QuerySet``, but applied across
multiple ``QuerySets``:

.. |QuerySets| replace:: ``QuerySets``
.. _QuerySets: https://docs.djangoproject.com/en/dev/ref/models/querysets/

* Methods that take a list of fields (e.g. ``filter()``, ``exclude()``,
  ``get()``, ``order_by()``) must use fields that are common across all
  sub-``QuerySets``.
* Relationships across related models work (e.g. ``'foo__bar'``, ``'foo'``, or
  ``'foo_id'``). syntax).
* The sub-``QuerySets`` are evaluated as late as possible (e.g. during
  iteration, slicing, pickling, ``repr()``/``len()``/``list()``/``bool()``
  calls).
* Public ``QuerySet`` API methods that are untested/unimplemented raise
  ``NotImplementedError``. ``AttributeError`` is raised on attributes not
  explictly inherited from ``QuerySet``.

.. Auto-generated content, run python gen_docs.py to generate this.
.. ATTRIBUTES_TABLE_START
.. ATTRIBUTES_TABLE_END
.. End auto-generate content.

Known Issues
============

* Cannot handle random ``order_by()``(e.g. ``order_by('?')``).
* The full ``QuerySet`` API is not complete.

Requirements
============

* Python (2.7)
* Django (1.8, 1.9)

Support for Python (3.3, 3.4, 3.5) is wanted. If you wish an older version of
Django to be supported, please submit a pull request.

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
