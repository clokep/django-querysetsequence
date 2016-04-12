Django QuerySetSequence
#######################

.. image:: https://travis-ci.org/percipient/django-querysetsequence.svg?branch=master
    :target: https://travis-ci.org/percipient/django-querysetsequence

.. image:: https://coveralls.io/repos/github/percipient/django-querysetsequence/badge.svg?branch=master
    :target: https://coveralls.io/github/percipient/django-querysetsequence?branch=master

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
.. |check| unicode:: U+2713
.. |xmark| unicode:: U+2717

.. list-table:: ``QuerySet`` API implemented by ``QuerySetSequence``
    :widths: 15 10 30
    :header-rows: 1

    * - Method
      - Implemented?
      - Notes
    * - |filter|_
      - |check|
      - 
    * - |exclude|_
      - |check|
      - 
    * - |annotate|_
      - |xmark|
      - 
    * - |order_by|_
      - |check|
      - Does not support random ``order_by()`` (e.g. ``order_by('?')``)
    * - |reverse|_
      - |check|
      - 
    * - |distinct|_
      - |xmark|
      - 
    * - |values|_
      - |xmark|
      - 
    * - |values_list|_
      - |xmark|
      - 
    * - |dates|_
      - |xmark|
      - 
    * - |datetimes|_
      - |xmark|
      - 
    * - |none|_
      - |check|
      - 
    * - |all|_
      - |check|
      - 
    * - |select_related|_
      - |check|
      - 
    * - |prefetch_related|_
      - |check|
      - 
    * - |extra|_
      - |xmark|
      - 
    * - |defer|_
      - |xmark|
      - 
    * - |only|_
      - |xmark|
      - 
    * - |using|_
      - |xmark|
      - 
    * - |select_for_update|_
      - |xmark|
      - 
    * - |raw|_
      - |xmark|
      - 
    * - |get|_
      - |check|
      - 
    * - |create|_
      - |xmark|
      - Cannot be implemented in ``QuerySetSequence``.
    * - |get_or_create|_
      - |xmark|
      - Cannot be implemented in ``QuerySetSequence``.
    * - |update_or_create|_
      - |xmark|
      - Cannot be implemented in ``QuerySetSequence``.
    * - |bulk_create|_
      - |xmark|
      - Cannot be implemented in ``QuerySetSequence``.
    * - |count|_
      - |check|
      - 
    * - |in_bulk|_
      - |xmark|
      - Cannot be implemented in ``QuerySetSequence``.
    * - |iterator|_
      - |check|
      - 
    * - |latest|_
      - |xmark|
      - 
    * - |earliest|_
      - |xmark|
      - 
    * - |first|_
      - |xmark|
      - 
    * - |last|_
      - |xmark|
      - 
    * - |aggregate|_
      - |xmark|
      - 
    * - |exists|_
      - |check|
      - 
    * - |update|_
      - |xmark|
      - Cannot be implemented in ``QuerySetSequence``.
    * - |delete|_
      - |check|
      - 
    * - |as_manager|_
      - |check|
      - 

.. |filter| replace:: ``filter()``
.. _filter: https://docs.djangoproject.com/en/dev/ref/models/querysets/#filter
.. |exclude| replace:: ``exclude()``
.. _exclude: https://docs.djangoproject.com/en/dev/ref/models/querysets/#exclude
.. |annotate| replace:: ``annotate()``
.. _annotate: https://docs.djangoproject.com/en/dev/ref/models/querysets/#annotate
.. |order_by| replace:: ``order_by()``
.. _order_by: https://docs.djangoproject.com/en/dev/ref/models/querysets/#order_by
.. |reverse| replace:: ``reverse()``
.. _reverse: https://docs.djangoproject.com/en/dev/ref/models/querysets/#reverse
.. |distinct| replace:: ``distinct()``
.. _distinct: https://docs.djangoproject.com/en/dev/ref/models/querysets/#distinct
.. |values| replace:: ``values()``
.. _values: https://docs.djangoproject.com/en/dev/ref/models/querysets/#values
.. |values_list| replace:: ``values_list()``
.. _values_list: https://docs.djangoproject.com/en/dev/ref/models/querysets/#values_list
.. |dates| replace:: ``dates()``
.. _dates: https://docs.djangoproject.com/en/dev/ref/models/querysets/#dates
.. |datetimes| replace:: ``datetimes()``
.. _datetimes: https://docs.djangoproject.com/en/dev/ref/models/querysets/#datetimes
.. |none| replace:: ``none()``
.. _none: https://docs.djangoproject.com/en/dev/ref/models/querysets/#none
.. |all| replace:: ``all()``
.. _all: https://docs.djangoproject.com/en/dev/ref/models/querysets/#all
.. |select_related| replace:: ``select_related()``
.. _select_related: https://docs.djangoproject.com/en/dev/ref/models/querysets/#select_related
.. |prefetch_related| replace:: ``prefetch_related()``
.. _prefetch_related: https://docs.djangoproject.com/en/dev/ref/models/querysets/#prefetch_related
.. |extra| replace:: ``extra()``
.. _extra: https://docs.djangoproject.com/en/dev/ref/models/querysets/#extra
.. |defer| replace:: ``defer()``
.. _defer: https://docs.djangoproject.com/en/dev/ref/models/querysets/#defer
.. |only| replace:: ``only()``
.. _only: https://docs.djangoproject.com/en/dev/ref/models/querysets/#only
.. |using| replace:: ``using()``
.. _using: https://docs.djangoproject.com/en/dev/ref/models/querysets/#using
.. |select_for_update| replace:: ``select_for_update()``
.. _select_for_update: https://docs.djangoproject.com/en/dev/ref/models/querysets/#select_for_update
.. |raw| replace:: ``raw()``
.. _raw: https://docs.djangoproject.com/en/dev/ref/models/querysets/#raw
.. |get| replace:: ``get()``
.. _get: https://docs.djangoproject.com/en/dev/ref/models/querysets/#get
.. |create| replace:: ``create()``
.. _create: https://docs.djangoproject.com/en/dev/ref/models/querysets/#create
.. |get_or_create| replace:: ``get_or_create()``
.. _get_or_create: https://docs.djangoproject.com/en/dev/ref/models/querysets/#get_or_create
.. |update_or_create| replace:: ``update_or_create()``
.. _update_or_create: https://docs.djangoproject.com/en/dev/ref/models/querysets/#update_or_create
.. |bulk_create| replace:: ``bulk_create()``
.. _bulk_create: https://docs.djangoproject.com/en/dev/ref/models/querysets/#bulk_create
.. |count| replace:: ``count()``
.. _count: https://docs.djangoproject.com/en/dev/ref/models/querysets/#count
.. |in_bulk| replace:: ``in_bulk()``
.. _in_bulk: https://docs.djangoproject.com/en/dev/ref/models/querysets/#in_bulk
.. |iterator| replace:: ``iterator()``
.. _iterator: https://docs.djangoproject.com/en/dev/ref/models/querysets/#iterator
.. |latest| replace:: ``latest()``
.. _latest: https://docs.djangoproject.com/en/dev/ref/models/querysets/#latest
.. |earliest| replace:: ``earliest()``
.. _earliest: https://docs.djangoproject.com/en/dev/ref/models/querysets/#earliest
.. |first| replace:: ``first()``
.. _first: https://docs.djangoproject.com/en/dev/ref/models/querysets/#first
.. |last| replace:: ``last()``
.. _last: https://docs.djangoproject.com/en/dev/ref/models/querysets/#last
.. |aggregate| replace:: ``aggregate()``
.. _aggregate: https://docs.djangoproject.com/en/dev/ref/models/querysets/#aggregate
.. |exists| replace:: ``exists()``
.. _exists: https://docs.djangoproject.com/en/dev/ref/models/querysets/#exists
.. |update| replace:: ``update()``
.. _update: https://docs.djangoproject.com/en/dev/ref/models/querysets/#update
.. |delete| replace:: ``delete()``
.. _delete: https://docs.djangoproject.com/en/dev/ref/models/querysets/#delete
.. |as_manager| replace:: ``as_manager()``
.. _as_manager: https://docs.djangoproject.com/en/dev/ref/models/querysets/#as_manager
.. ATTRIBUTES_TABLE_END
.. End auto-generate content.

Requirements
============

* Python (2.7, 3.4, 3.5)
* Django (1.8, 1.9)

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

You can also provide a ``model`` keyword argument if you need to specify the
``QuerySet`` ``Model``, e.g. for compatibility with some third-party
applications that check the ``model`` field for equality

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
