.. :changelog:

Changelog
#########

next
====


0.14 (2021-02-26)
=================

Features
--------

* Support Django 3.2 (`#78 <https://github.com/clokep/django-querysetsequence/pull/78>`_,
  `#81 <https://github.com/clokep/django-querysetsequence/pull/81>`_)
* Support Python 3.9. (`#78 <https://github.com/clokep/django-querysetsequence/pull/78>`_)
* Support the ``values()`` and ``values_list()`` methods.
  (`#73 <https://github.com/clokep/django-querysetsequence/pull/73>`_,
  `#74 <https://github.com/clokep/django-querysetsequence/pull/74>`_)
* Support the ``distinct()`` method when each ``QuerySet`` instance is from a
  unique model. Contributed by
  `@jpic <https://github.com/jpic>`_. (`#77 <https://github.com/clokep/django-querysetsequence/pull/77>`_,
  `#80 <https://github.com/clokep/django-querysetsequence/pull/80>`_)
* Add `Sphinx documentation <https://django-querysetsequence.readthedocs.io/>`_
  which is available at Read the Docs.

Bugfixes
--------

* Support calling ``filter()`` with |Q() objects|_. Contributed by
  `@jpic <https://github.com/jpic>`_. (`#76 <https://github.com/clokep/django-querysetsequence/pull/76>`_)

.. |Q() objects| replace:: ``Q()`` objects
.. _Q() objects: https://docs.djangoproject.com/en/dev/ref/models/querysets/#q-objects

Miscellaneous
-------------

* Add an additional test for the interaction of ``order_by()`` and ``only()``.
  (`#72 <https://github.com/clokep/django-querysetsequence/pull/72>`_)
* Support Django REST Framework 3.12. (`#75 <https://github.com/clokep/django-querysetsequence/pull/75>`_)
* Switch continuous integration to GitHub Actions. (`#79 <https://github.com/clokep/django-querysetsequence/pull/79>`_)
* Drop support for Python 3.5. (`#82 <https://github.com/clokep/django-querysetsequence/pull/82>`_)


0.13 (2020-07-27)
=================

Features
--------

* Support Django 3.1. (`#69 <https://github.com/clokep/django-querysetsequence/pull/69>`_)
* Drop support for Django < 2.2.  (`#70 <https://github.com/clokep/django-querysetsequence/pull/70>`_)

Bugfixes
--------

* ``explain()`` now passes through parameters to the underlying ``QuerySet`` instances.
  (`#69 <https://github.com/clokep/django-querysetsequence/pull/69>`_)
* Fixes compatibility issue with ``ModelChoiceField``. Contributed by
  `@jpic <https://github.com/jpic>`_. (`#68 <https://github.com/clokep/django-querysetsequence/pull/68>`_)

Miscellaneous
-------------

* Drop support for Django < 2.2.  (`#70 <https://github.com/clokep/django-querysetsequence/pull/70>`_)


0.12 (2019-12-20)
=================

Bugfixes
--------

* Do not use ``is not`` to compare to an integer literal.  (`#61 <https://github.com/clokep/django-querysetsequence/pull/61>`_)

Miscellaneous
-------------

* Support Django 3.0. (`#59 <https://github.com/clokep/django-querysetsequence/pull/59>`_)
* Support Python 3.8. (`#59 <https://github.com/clokep/django-querysetsequence/pull/59>`_)
* Support Django REST Framework 3.10 and 3.11. (`#59 <https://github.com/clokep/django-querysetsequence/pull/59>`_,
  `#64 <https://github.com/clokep/django-querysetsequence/pull/64>`_)
* Drop support for Python 2.7. (`#59 <https://github.com/clokep/django-querysetsequence/pull/59>`_)
* Drop support for Django 2.0 and 2.1. (`#59 <https://github.com/clokep/django-querysetsequence/pull/59>`_)


0.11 (2019-04-25)
=================

Features
--------

* Add a ``QuerySetSequence`` specific method: ``get_querysets()``. Contributed by
  `@optiz0r <https://github.com/optiz0r>`_. (`#53 <https://github.com/clokep/django-querysetsequence/pull/53>`_)

Miscellaneous
-------------

* Support Django 2.2. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#51 <https://github.com/clokep/django-querysetsequence/pull/51>`_)
* Support Django REST Framework 3.9. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#51 <https://github.com/clokep/django-querysetsequence/pull/51>`_)
* Support Python 3.7. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#51 <https://github.com/clokep/django-querysetsequence/pull/51>`_)
* Drop support for Django REST Framework < 3.6.3. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#51 <https://github.com/clokep/django-querysetsequence/pull/51>`_)
* Drop support for Python 3.4. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#51 <https://github.com/clokep/django-querysetsequence/pull/51>`_)


0.10 (2018-10-09)
=================

Features
--------

* Support ``first()``, ``last()``, ``latest()``, and ``earliest()`` methods.
  (`#40 <https://github.com/clokep/django-querysetsequence/pull/40>`_,
  `#49 <https://github.com/clokep/django-querysetsequence/pull/49>`_)
* Support the ``&`` and ``|`` operators. (`#41 <https://github.com/clokep/django-querysetsequence/pull/41>`_)
* Support ``defer()`` and ``only()`` methods to control which fields are returned.
  (`#44 <https://github.com/clokep/django-querysetsequence/pull/44>`_)
* Support calling ``using()`` to switch databases for an entire ``QuerySetSequence``.
  (`#44 <https://github.com/clokep/django-querysetsequence/pull/44>`_)
* Support calling ``extra()`, ``update()``, and ``annotate()`` which get applied
  to each ``QuerySet``. (`#46 <https://github.com/clokep/django-querysetsequence/pull/46>`_,
  `#47 <https://github.com/clokep/django-querysetsequence/pull/47>`_)
* Support calling ``explain()`` on Django >= 2.1. (`#48 <https://github.com/clokep/django-querysetsequence/pull/48>`_)

Bugfixes
--------

* Raise ``NotImplementedError`` on unimplemented methods. This fixes a regression
  introduced in 0.9. (`#42 <https://github.com/clokep/django-querysetsequence/pull/42>`_)
* Expand tests for empty ``QuerySet`` instances. (`#43 <https://github.com/clokep/django-querysetsequence/pull/43>`_)

0.9 (2018-09-20)
================

Bugfixes
--------

* Stop using the internals of QuerySet for better forward compatibility. This change
  means that ``QuerySetSequence`` is no longer a sub-class of ``QuerySet`` and
  should improve interactions with other packages which modify ``QuerySet``.
  (`#38 <https://github.com/clokep/django-querysetsequence/pull/38>`_)

Miscellaneous
-------------

* Support Django REST Framework 3.7 and 3.8.
  (`#33 <https://github.com/clokep/django-querysetsequence/pull/33>`_,
  `#39 <https://github.com/clokep/django-querysetsequence/pull/39>`_)
* Support Django 2.0 and 2.1. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#35 <https://github.com/clokep/django-querysetsequence/pull/35>`_,
  `#39 <https://github.com/clokep/django-querysetsequence/pull/39>`_)
* Drop support for Django < 1.11. Django 1.11 and above
  are supported. This also drops support for Django REST Framework < 3.4, since
  they do not support Django 1.11. (`#36 <https://github.com/clokep/django-querysetsequence/pull/36>`_)


0.8 (2017-09-05)
================

Features
--------

* Optimize iteration when *not* slicing a ``QuerySetSequence``. Contributed by
  `@EvgeneOskin <https://github.com/EvgeneOskin>`_.
  (`#29 <https://github.com/clokep/django-querysetsequence/pull/29>`_)

Miscellaneous
-------------

* Support Django 1.11. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#26 <https://github.com/clokep/django-querysetsequence/pull/26>`_,
  `#32 <https://github.com/clokep/django-querysetsequence/pull/32>`_)
* Support Django REST Framework 3.5 and 3.6.
  (`#26 <https://github.com/clokep/django-querysetsequence/pull/26>`_)


0.7.2 (2017-04-04)
==================

Bugfixes
--------

* Calling an unimplemented method with parameters on ``QuerySetSequence`` raised
  a non-sensical error. (`#28 <https://github.com/clokep/django-querysetsequence/pull/28>`_)

0.7.1 (2017-03-31)
==================

Bugfixes
--------

* Slicing a ``QuerySetSequence`` did not work properly when the slice reduced the
  ``QuerySetSequence`` to a single ``QuerySet``.
  (`#23 <https://github.com/clokep/django-querysetsequence/pull/23>`_,
  `#24 <https://github.com/clokep/django-querysetsequence/pull/24>`_)
* Typo fixes. (`#19 <https://github.com/clokep/django-querysetsequence/pull/19>`_)

Miscellaneous
-------------

* Support Django REST Framework 3.5. (`#20 <https://github.com/clokep/django-querysetsequence/pull/20>`_)


0.7 (2016-10-20)
================

Features
--------

* Allow filtering / querying / ordering by the order of the ``QuerySets`` in the
  ``QuerySetSequence`` by using ``'#'``. This allows for additional optimizations
  when using third-party applications, e.g. Django REST Framework.
  (`#10 <https://github.com/clokep/django-querysetsequence/pull/10>`_,
  `#14 <https://github.com/clokep/django-querysetsequence/pull/14>`_,
  `#15 <https://github.com/clokep/django-querysetsequence/pull/15>`_,
  `#16 <https://github.com/clokep/django-querysetsequence/pull/16>`_)
* `Django REST Framework`_ integration: includes a subclass of the
  ``CursorPagination`` from Django REST Framework under
  ``queryset_sequence.pagination.SequenceCursorPagination`` which is designed to
  work efficiently with a ``QuerySetSequence`` by first ordering by internal
  ``QuerySet``, then by the ``ordering`` attribute. (`#17 <https://github.com/clokep/django-querysetsequence/pull/17>`_)
* Move ``queryset_sequence`` to an actual module in order to hide some
  implementation details. (`#11 <https://github.com/clokep/django-querysetsequence/pull/11>`_)

Bugfixes
--------

* ``PartialInheritanceMeta`` must be provided ``INHERITED_ATTRS`` and
  ``NOT_IMPLEMENTED_ATTRS``. (`#12 <https://github.com/clokep/django-querysetsequence/pull/12>`_)

.. _Django REST Framework: http://www.django-rest-framework.org/


0.6.1 (2016-08-03)
==================

Miscellaneous
-------------

* Support Django 1.10. (`#9 <https://github.com/clokep/django-querysetsequence/pull/9>`_)


0.6 (2016-06-07)
================

Features
--------

* Allow specifying the ``Model`` to use when instantiating a ``QuerySetSequence``.
  This is required for compatibility with some third-party applications that check
  the ``model`` field for equality, e.g. when using the ``DjangoFilterBackend``
  with Django REST Framework. Contributed by `@CountZachula <https://github.com/CountZachula>`_.
  (`#6 <https://github.com/clokep/django-querysetsequence/pull/6>`_)
* Support ``prefetch_related``. (`#7 <https://github.com/clokep/django-querysetsequence/pull/7>`_)

Bugfixes
--------

* Fixes an issue when using Django Debug Toolbar. (`#8 <https://github.com/clokep/django-querysetsequence/pull/8>`_)


0.5 (2016-02-21)
================

Features
--------

* Significant performance improvements when ordering the
  ``QuerySetSequence``. (`#5 <https://github.com/clokep/django-querysetsequence/pull/5>`_)
* Support ``delete()`` to remove items.


0.4 (2016-02-03)
================

Miscellaneous
-------------

* Python 3.4/3.5 support. Contributed by `@jpic <https://github.com/jpic>`_.
  (`#3 <https://github.com/clokep/django-querysetsequence/pull/3>`_)


0.3 (2016-01-29)
================

Features
--------

* Raises ``NotImplementedError`` for ``QuerySet`` methods that ``QuerySetSequence`` does not implement.
* Support ``reverse()`` to reverse the item ordering
* Support ``none()`` to return an ``EmptyQuerySet``
* Support ``exists()`` to check if a ``QuerySetSequence`` has any results.
* Support ``select_related`` to follow foreign-key relationships when generating results.

Bugfixes
--------

* Do not evaluate any ``QuerySets`` when calling ``filter()`` or ``exclude()``
  like a Django ``QuerySet``. Contributed by
  `@jpic <https://github.com/jpic>`_. (`#1 <https://github.com/clokep/django-querysetsequence/pull/1>`_)
* Do not cache the results when calling ``iterator()``.


0.2.4 (2016-01-21)
==================

Features
--------

* Support ``order_by()`` that references a related model (e.g. a ``ForeignKey``
  relationship using ``foo`` or ``foo_id`` syntaxes)
* Support ``order_by()`` that references a field on a related model (e.g.
  ``foo__bar``)

Miscellaneous
-------------

* Add support for Django 1.9.1


0.2.3 (2016-01-11)
==================

Bugfixes
--------

* Fixed calling ``order_by()`` with a single field


0.2.2 (2016-01-08)
==================

Features
--------

* Support the ``get()`` method on ``QuerySetSequence``


0.2.1 (2016-01-08)
==================

Bugfixes
--------

* Fixed a bug when there's no data to iterate.


0.2 (2016-01-08)
================

Bugfixes
--------

* Do not try to instantiate ``EmptyQuerySet``.

Miscellaneous
-------------

* Fixed packaging for pypi.


0.1 (2016-01-07)
================

* Initial release to support Django 1.8.8

The initial commits on based on DjangoSnippets and other code:

* `DjangoSnippet 1103 <https://www.djangosnippets.org/snippets/1103/>`_ by
  `mattdw <https://www.djangosnippets.org/users/mattdw/>`_.
* `DjangoSnippet 1253 <https://djangosnippets.org/snippets/1253/>`_ by
  `joonas <https://djangosnippets.org/users/joonas/>`_ and some bugfixes in the comments:

  * Updated per `comment 1553 <https://djangosnippets.org/snippets/1253/#c1553>`_ by `nosa_manuel <https://djangosnippets.org/users/nosa_manuel/>`_.
  * Updated per `comment 4642 <https://djangosnippets.org/snippets/1253/#c4642>`_ by `esquevin <https://djangosnippets.org/users/esquevin/>`_.
* `DjangoSnippet 1933 <https://djangosnippets.org/snippets/1933/>`_ by
  `t_rybik <https://djangosnippets.org/users/t_rybik/>`_.
* `django-ko-demo from The Atlantic <https://github.com/theatlantic/django-ko-demo/blob/1a37c9ad9bcd68a40c35462fb819fff85a9533f7/apps/curation_nouveau/queryset_sequence.py>`_
  by `@fdintino <https://github.com/fdintino>`_.
