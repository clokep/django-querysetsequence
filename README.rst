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
  ``NotImplementedError``.

.. Auto-generated content, run python gen_docs.py to generate this.
.. ATTRIBUTES_TABLE_START
.. |check| unicode:: U+2713
.. |xmark| unicode:: U+2717

``QuerySet`` API implemented by ``QuerySetSequence``
----------------------------------------------------

.. list-table:: Methods that return new ``QuerySets``
    :widths: 15 10 30
    :header-rows: 1

    * - Method
      - Implemented?
      - Notes

    * - |filter|_
      - |check|
      - See [1]_ for information on the ``QuerySet`` lookup: ``'#'``.
    * - |exclude|_
      - |check|
      - See [1]_ for information on the ``QuerySet`` lookup: ``'#'``.
    * - |annotate|_
      - |check|
      -
    * - |order_by|_
      - |check|
      - Does not support random ordering (e.g. ``order_by('?')``). See [1]_ for
        information on the ``QuerySet`` lookup: ``'#'``.
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
    * - |union|_
      - |xmark|
      -
    * - |intersection|_
      - |xmark|
      -
    * - |difference|_
      - |xmark|
      -
    * - |select_related|_
      - |check|
      -
    * - |prefetch_related|_
      - |check|
      -
    * - |extra|_
      - |check|
      -
    * - |defer|_
      - |check|
      -
    * - |only|_
      - |check|
      -
    * - |using|_
      - |check|
      -
    * - |select_for_update|_
      - |xmark|
      -
    * - |raw|_
      - |xmark|
      -

.. list-table:: Operators that return new ``QuerySets``
    :widths: 15 10 30
    :header-rows: 1

    * - Operator
      - Implemented?
      - Notes

    * - |AND (&)|_
      - |check|
      - A ``QuerySetSequence`` can be combined with a ``QuerySet``. The
        ``QuerySets`` in the ``QuerySetSequence`` are filtered to ones matching
        the same ``Model``. Each of those is ANDed with the other ``QuerySet``.
    * - |OR (\|)|_
      - |check|
      - A ``QuerySetSequence`` can be combined with a ``QuerySet`` or
        ``QuerySetSequence``. When combining with a ``QuerySet``, it is added to
        the ``QuerySetSequence``. Combiningg with another ``QuerySetSequence``
        adds together the two underlying sets of ``QuerySets``.

.. list-table:: Methods that do not return ``QuerySets``
    :widths: 15 10 30
    :header-rows: 1

    * - Method
      - Implemented?
      - Notes

    * - |get|_
      - |check|
      - See [1]_ for information on the ``QuerySet`` lookup: ``'#'``.
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
      - |check|
      - If no fields are given, ``get_latest_by`` on each model is required to
        be identical.
    * - |earliest|_
      - |check|
      - See the docuemntation for ``latest()``.
    * - |first|_
      - |check|
      - If no ordering is set this is essentially the same as calling
        ``first()`` on the first ``QuerySet``, if there is an ordering, the
        result of ``first()`` for each ``QuerySet`` is compared and the "first"
        value is returned.
    * - |last|_
      - |check|
      - See the documentation for ``first()``.
    * - |aggregate|_
      - |xmark|
      -
    * - |exists|_
      - |check|
      -
    * - |update|_
      - |check|
      -
    * - |delete|_
      - |check|
      -
    * - |as_manager|_
      - |check|
      -
    * - |explain|_
      - |check|
      - Only available on Django >= 2.1.

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
.. _values_list: https://docs.djangoproject.com/en/dev/ref/models/querysets/#values-list
.. |dates| replace:: ``dates()``
.. _dates: https://docs.djangoproject.com/en/dev/ref/models/querysets/#dates
.. |datetimes| replace:: ``datetimes()``
.. _datetimes: https://docs.djangoproject.com/en/dev/ref/models/querysets/#datetimes
.. |none| replace:: ``none()``
.. _none: https://docs.djangoproject.com/en/dev/ref/models/querysets/#none
.. |all| replace:: ``all()``
.. _all: https://docs.djangoproject.com/en/dev/ref/models/querysets/#all
.. |union| replace:: ``union()``
.. _union: https://docs.djangoproject.com/en/dev/ref/models/querysets/#union
.. |intersection| replace:: ``intersection()``
.. _intersection: https://docs.djangoproject.com/en/dev/ref/models/querysets/#intersection
.. |difference| replace:: ``difference()``
.. _difference: https://docs.djangoproject.com/en/dev/ref/models/querysets/#difference
.. |select_related| replace:: ``select_related()``
.. _select_related: https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-related
.. |prefetch_related| replace:: ``prefetch_related()``
.. _prefetch_related: https://docs.djangoproject.com/en/dev/ref/models/querysets/#prefetch-related
.. |extra| replace:: ``extra()``
.. _extra: https://docs.djangoproject.com/en/dev/ref/models/querysets/#extra
.. |defer| replace:: ``defer()``
.. _defer: https://docs.djangoproject.com/en/dev/ref/models/querysets/#defer
.. |only| replace:: ``only()``
.. _only: https://docs.djangoproject.com/en/dev/ref/models/querysets/#only
.. |using| replace:: ``using()``
.. _using: https://docs.djangoproject.com/en/dev/ref/models/querysets/#using
.. |select_for_update| replace:: ``select_for_update()``
.. _select_for_update: https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-for-update
.. |raw| replace:: ``raw()``
.. _raw: https://docs.djangoproject.com/en/dev/ref/models/querysets/#raw

.. |AND (&)| replace:: AND (``&``)
.. _AND (&): https://docs.djangoproject.com/en/dev/ref/models/querysets/#and
.. |OR (|)| replace:: OR (``|``)
.. _OR (\|): https://docs.djangoproject.com/en/dev/ref/models/querysets/#or

.. |get| replace:: ``get()``
.. _get: https://docs.djangoproject.com/en/dev/ref/models/querysets/#get
.. |create| replace:: ``create()``
.. _create: https://docs.djangoproject.com/en/dev/ref/models/querysets/#create
.. |get_or_create| replace:: ``get_or_create()``
.. _get_or_create: https://docs.djangoproject.com/en/dev/ref/models/querysets/#get-or-create
.. |update_or_create| replace:: ``update_or_create()``
.. _update_or_create: https://docs.djangoproject.com/en/dev/ref/models/querysets/#update-or-create
.. |bulk_create| replace:: ``bulk_create()``
.. _bulk_create: https://docs.djangoproject.com/en/dev/ref/models/querysets/#bulk-create
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
.. _as_manager: https://docs.djangoproject.com/en/dev/ref/models/querysets/#as-manager
.. |explain| replace:: ``explain()``
.. _explain: https://docs.djangoproject.com/en/dev/ref/models/querysets/#explain

.. [1]  ``QuerySetSequence`` supports a special field lookup that looks up the
        index of the ``QuerySet``, this is represented by ``'#'``. This can be
        used in any of the operations that normally take field lookups (i.e.
        ``filter()``, ``exclude()``, and ``get()``), as well as ``order_by()``.

        A few examples are below:

        .. code-block:: python

            # Order first by QuerySet, then by the value of the 'title' field.
            QuerySetSequence(...).order_by('#', 'title')

            # Filter out the first QuerySet.
            QuerySetSequence(...).filter(**{'#__gt': 0})

        .. note::

            Ordering first by ``QuerySet`` allows for a more optimized code path
            when iterating over the entries.

        .. warning::

            Not all lookups are supported when using ``'#'`` (some lookups
            simply don't make sense; others are just not supported). The
            following are allowed:

            * ``exact``
            * ``iexact``
            * ``contains``
            * ``icontains``
            * ``in``
            * ``gt``
            * ``gte``
            * ``lt``
            * ``lte``
            * ``startswith``
            * ``istartswith``
            * ``endswith``
            * ``iendswith``
            * ``range``

Requirements
============

* Python (2.7, 3.5, 3.6, 3.7)
* Django (1.11, 2.0, 2.1)
* (Optionally) `Django REST Framework`_ (3.6.3+, 3.7, 3.8, 3.9)

.. _Django REST Framework: http://www.django-rest-framework.org/

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

Django REST Framework integration
=================================

django-querysetsequence comes with a custom ``CursorPagination`` class that
helps integration with Django REST Framework. It is optimized to iterate over a
``QuerySetSequence`` first by ``QuerySet`` and then by the normal ``ordering``
configuration. This uses the optimized code-path for iteration that avoids
interleaving the individual ``QuerySets``. For example:

.. code-block:: python

    from queryset_sequence.pagination import SequenceCursorPagination

    class PublicationPagination(SequenceCursorPagination):
        ordering = ['author', 'title']

    class PublicationViewSet(viewsets.ModelViewSet):
        pagination_class = PublicationPagination

        def get_queryset(self):
            # This will return all Books first, then all Articles. Each of those
            # is individually ordered by ``author``, then ``title``.
            return QuerySetSequence(Book.objects.all(), Article.objects.all())

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
