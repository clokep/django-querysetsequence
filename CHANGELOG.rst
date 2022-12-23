.. :changelog:

Changelog
#########

next
====

Bugfixes
--------

* ``None`` values are now appropriately sorted first or last (depending on database
  support. Contributed by `@vuongdv-spinshell <https://github.com/vuongdv-spinshell>`_.
  (`#97 <https://github.com/clokep/django-querysetsequence/pull/97>`_)

Improvements
------------

* Initial support for `asynchronous queries`_. (`#99 <https://github.com/clokep/django-querysetsequence/pull/99>`_)

.. _asynchronous queries: https://docs.djangoproject.com/en/4.1/topics/db/queries/#async-queries

Maintenance
-----------

* Support Django 4.0 and 4.1. (`#83 <https://github.com/clokep/django-querysetsequence/pull/83>`_)
* Support Django REST Framework 4.14. (`#101 <https://github.com/clokep/django-querysetsequence/pull/101>`_)
* Drop support for Django 2.2 and 3.1. (`#98 <https://github.com/clokep/django-querysetsequence/pull/98>`_)
* Drop support for Django REST Framework < 3.11. (`#98 <https://github.com/clokep/django-querysetsequence/pull/98>`_)


0.16 (2022-04-01)
=================

Improvements
------------

* Fix ``QuerySetSequence``'s support with Django REST Framework's ``DjangoFilterBackend``
  by accepting a ``model`` parameter. If one is not provided, a dummy model is
  used to provide a reasonable ``DoesNotExist`` error. Contributed by
  `@j0nm1 <https://github.com/j0nm1>`_. (`#88 <https://github.com/clokep/django-querysetsequence/pull/88>`_)

Maintenance
-----------

* Support Python 3.10. (`#86 <https://github.com/clokep/django-querysetsequence/pull/86>`_)
* Support Django REST Framework 3.13. (`#86 <https://github.com/clokep/django-querysetsequence/pull/86>`_)
* Drop support for Python 3.6. (`3fc1d0f <https://github.com/clokep/django-querysetsequence/commit/3fc1d0f8b1ad3727d54ef6c2d0761804455331e2>`_)
* Improve package metadata. (`#89 <https://github.com/clokep/django-querysetsequence/pull/89>`_)
* Run `black <https://black.readthedocs.io/>`_, `isort <https://pycqa.github.io/isort/>`_,
  and `flake8 <https://flake8.pycqa.org>`_, and `pyupgrade <https://github.com/asottile/pyupgrade>`_.
  (`#90 <https://github.com/clokep/django-querysetsequence/pull/90>`_,
  `#91 <https://github.com/clokep/django-querysetsequence/pull/91>`_)


0.15 (2021-12-10)
=================

Improvements
------------

* Support the ``contains()`` method. (`#85 <https://github.com/clokep/django-querysetsequence/pull/85>`_)

Maintenance
-----------

* Support Django 4.0. (`#83 <https://github.com/clokep/django-querysetsequence/pull/83>`_)
* Drop support for Django 3.0. (`#83 <https://github.com/clokep/django-querysetsequence/pull/83>`_)
* Changed packaging to use setuptools declarative config in ``setup.cfg``.
  (`#84 <https://github.com/clokep/django-querysetsequence/pull/84>`_)


0.14 (2021-02-26)
=================

Improvements
------------

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

Maintenance
-----------

* Support Python 3.9. (`#78 <https://github.com/clokep/django-querysetsequence/pull/78>`_)
* Support Django 3.2. (`#78 <https://github.com/clokep/django-querysetsequence/pull/78>`_,
  `#81 <https://github.com/clokep/django-querysetsequence/pull/81>`_)
* Support Django REST Framework 3.12. (`#75 <https://github.com/clokep/django-querysetsequence/pull/75>`_)
* Drop support for Python 3.5. (`#82 <https://github.com/clokep/django-querysetsequence/pull/82>`_)
* Add an additional test for the interaction of ``order_by()`` and ``only()``.
  (`#72 <https://github.com/clokep/django-querysetsequence/pull/72>`_)
* Switch continuous integration to GitHub Actions. (`#79 <https://github.com/clokep/django-querysetsequence/pull/79>`_)


0.13 (2020-07-27)
=================

Bugfixes
--------

* ``explain()`` now passes through parameters to the underlying ``QuerySet`` instances.
  (`#69 <https://github.com/clokep/django-querysetsequence/pull/69>`_)
* Fixes compatibility issue with ``ModelChoiceField``. Contributed by
  `@jpic <https://github.com/jpic>`_. (`#68 <https://github.com/clokep/django-querysetsequence/pull/68>`_)

Maintenance
-----------

* Support Django 3.1. (`#69 <https://github.com/clokep/django-querysetsequence/pull/69>`_)
* Drop support for Django < 2.2.  (`#70 <https://github.com/clokep/django-querysetsequence/pull/70>`_)


0.12 (2019-12-20)
=================

Bugfixes
--------

* Do not use ``is not`` to compare to an integer literal.  (`#61 <https://github.com/clokep/django-querysetsequence/pull/61>`_)

Maintenance
-----------

* Support Python 3.8. (`#59 <https://github.com/clokep/django-querysetsequence/pull/59>`_)
* Support Django 3.0. (`#59 <https://github.com/clokep/django-querysetsequence/pull/59>`_)
* Support Django REST Framework 3.10 and 3.11. (`#59 <https://github.com/clokep/django-querysetsequence/pull/59>`_,
  `#64 <https://github.com/clokep/django-querysetsequence/pull/64>`_)
* Drop support for Python 2.7. (`#59 <https://github.com/clokep/django-querysetsequence/pull/59>`_)
* Drop support for Django 2.0 and 2.1. (`#59 <https://github.com/clokep/django-querysetsequence/pull/59>`_)


0.11 (2019-04-25)
=================

Improvements
------------

* Add a ``QuerySetSequence`` specific method: ``get_querysets()``. Contributed by
  `@optiz0r <https://github.com/optiz0r>`_. (`#53 <https://github.com/clokep/django-querysetsequence/pull/53>`_)

Maintenance
-----------

* Support Python 3.7. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#51 <https://github.com/clokep/django-querysetsequence/pull/51>`_)
* Support Django 2.2. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#51 <https://github.com/clokep/django-querysetsequence/pull/51>`_)
* Support Django REST Framework 3.9. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#51 <https://github.com/clokep/django-querysetsequence/pull/51>`_)
* Drop support for Python 3.4. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#51 <https://github.com/clokep/django-querysetsequence/pull/51>`_)
* Drop support for Django REST Framework < 3.6.3. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#51 <https://github.com/clokep/django-querysetsequence/pull/51>`_)


0.10 (2018-10-09)
=================

Improvements
------------

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

* Stop using the internals of `QuerySet` for better forward compatibility. This change
  means that ``QuerySetSequence`` is no longer a sub-class of ``QuerySet`` and
  should improve interactions with other packages which modify ``QuerySet``.
  (`#38 <https://github.com/clokep/django-querysetsequence/pull/38>`_)

Maintenance
-----------

* Support Django 2.0 and 2.1. Contributed by
  `@michael-k <https://github.com/michael-k>`_. (`#35 <https://github.com/clokep/django-querysetsequence/pull/35>`_,
  `#39 <https://github.com/clokep/django-querysetsequence/pull/39>`_)
* Support Django REST Framework 3.7 and 3.8.
  (`#33 <https://github.com/clokep/django-querysetsequence/pull/33>`_,
  `#39 <https://github.com/clokep/django-querysetsequence/pull/39>`_)
* Drop support for Django < 1.11. (`#36 <https://github.com/clokep/django-querysetsequence/pull/36>`_)
* Drop support for Django REST Framework < 3.4.
  (`#36 <https://github.com/clokep/django-querysetsequence/pull/36>`_)


0.8 (2017-09-05)
================

Improvements
------------

* Optimize iteration when *not* slicing a ``QuerySetSequence``. Contributed by
  `@EvgeneOskin <https://github.com/EvgeneOskin>`_.
  (`#29 <https://github.com/clokep/django-querysetsequence/pull/29>`_)

Maintenance
-----------

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

Maintenance
-----------

* Support Django REST Framework 3.5. (`#20 <https://github.com/clokep/django-querysetsequence/pull/20>`_)


0.7 (2016-10-20)
================

Improvements
------------

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

Bugfixes
--------

* ``PartialInheritanceMeta`` must be provided ``INHERITED_ATTRS`` and
  ``NOT_IMPLEMENTED_ATTRS``. (`#12 <https://github.com/clokep/django-querysetsequence/pull/12>`_)

.. _Django REST Framework: http://www.django-rest-framework.org/

Maintenance
-----------

* Move ``queryset_sequence`` to an actual module in order to hide some
  implementation details. (`#11 <https://github.com/clokep/django-querysetsequence/pull/11>`_)


0.6.1 (2016-08-03)
==================

Maintenance
-----------

* Support Django 1.10. (`#9 <https://github.com/clokep/django-querysetsequence/pull/9>`_)


0.6 (2016-06-07)
================

Improvements
------------

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

Improvements
------------

* Significant performance improvements when ordering the
  ``QuerySetSequence``. (`#5 <https://github.com/clokep/django-querysetsequence/pull/5>`_)
* Support ``delete()`` to remove items. (`1bb1716 <https://github.com/clokep/django-querysetsequence/commit/1bb1716eeedb37d6323f5578de565eaf09cc94b3>`_)


0.4 (2016-02-03)
================

Maintenance
-----------

* Support Python 3.4 and 3.5. Contributed by `@jpic <https://github.com/jpic>`_.
  (`#3 <https://github.com/clokep/django-querysetsequence/pull/3>`_)


0.3 (2016-01-29)
================

Improvements
------------

* Raises ``NotImplementedError`` for ``QuerySet`` methods that ``QuerySetSequence``
  does not implement. (`e2c67c5 <https://github.com/clokep/django-querysetsequence/commit/e2c67c5070cbd7a88249b3537c14b9536d4eaee4>`_,
  `b376b87 <https://github.com/clokep/django-querysetsequence/commit/b376b877bd26a79095fe4e16d69d54f890a56524>`_)
* Support ``reverse()`` to reverse the item ordering. (`f27b2c7 <https://github.com/clokep/django-querysetsequence/commit/f27b2c76432e1e7ed7092056671cd5e9f6ed4b59>`_)
* Support ``none()`` to return an ``EmptyQuerySet``. (`6171c11 <https://github.com/clokep/django-querysetsequence/commit/6171c1113adc55d4fd16fea762233580ff992112>`_)
* Support ``exists()`` to check if a ``QuerySetSequence`` has any results. (`1aa705b <1aa705b53cebd8dde028d2bd1e2380db8b301049>`_)
* Support ``select_related`` to follow foreign-key relationships when generating results.
  (`ad54d5e <https://github.com/clokep/django-querysetsequence/commit/ad54d5ee6e4ce6b45a057b56e93ff674e46eba00>`_)

Bugfixes
--------

* Do not evaluate any ``QuerySets`` when calling ``filter()`` or ``exclude()``
  like a Django ``QuerySet``. Contributed by
  `@jpic <https://github.com/jpic>`_. (`#1 <https://github.com/clokep/django-querysetsequence/pull/1>`_,
  `baaf448 <https://github.com/clokep/django-querysetsequence/commit/baaf4484649cbec5c1f80c684b1fa4177b6e23fd>`_)
* Do not cache the results when calling ``iterator()``. (`6566a91 <https://github.com/clokep/django-querysetsequence/commit/6566a910e3cd3e71dc2b02859530e35487d55c21>`_)


0.2.4 (2016-01-21)
==================

Improvements
------------

* Support ``order_by()`` that references a related model (e.g. a ``ForeignKey``
  relationship using ``foo`` or ``foo_id`` syntaxes).
  (`94274d6 <https://github.com/clokep/django-querysetsequence/commit/94274d61e804827aa858cd0d0247f6400ece91a9>`_)
* Support ``order_by()`` that references a field on a related model (e.g.
  ``foo__bar``) (`a97d940 <https://github.com/clokep/django-querysetsequence/commit/a97d9406e2e40590f54c6861c6d33187e22dba9b>`_)

Maintenance
-----------

* Support Django 1.9.1. (`9497e09 <https://github.com/clokep/django-querysetsequence/commit/9497e09884e645af1f1016dbf91e49d8f21d1028>`_)


0.2.3 (2016-01-11)
==================

Bugfixes
--------

* Fixed calling ``order_by()`` with a single field.
  (`5c8521c <https://github.com/clokep/django-querysetsequence/commit/5c8521ce6b3da1f7a736b58f30b2f5a3019fef67>`_)


0.2.2 (2016-01-08)
==================

Improvements
------------

* Support the ``get()`` method on ``QuerySetSequence``.
  (`957a650 <https://github.com/clokep/django-querysetsequence/commit/957a65065f9ee23deb6936cd9444605fd3047bee>`_)


0.2.1 (2016-01-08)
==================

Bugfixes
--------

* Fixed a bug when there's no data to iterate.
  (`02aafac <https://github.com/clokep/django-querysetsequence/commit/02aafacaad4049e6143d262027474e08a341751a>`_)


0.2 (2016-01-08)
================

Bugfixes
--------

* Do not try to instantiate ``EmptyQuerySet``.
  (`99dba06 <https://github.com/clokep/django-querysetsequence/commit/99dba0613c9acfd99197b28114323502932df1aa>`_)

Maintenance
-----------

* Fixed packaging. (`9b1ae74 <https://github.com/clokep/django-querysetsequence/commit/9b1ae7410004635dd59d07fda89c9aa93979a88f>`_)


0.1 (2016-01-07)
================

* Support Django 1.8.0.
* Various bug fixes and tests.

The initial commits on based on DjangoSnippets and other code:

* `DjangoSnippet 1103 <https://www.djangosnippets.org/snippets/1103/>`_ by
  `mattdw <https://www.djangosnippets.org/users/mattdw/>`_. foo_7a081bfcfc0eff2aba4d550632d9733786c65ac8
* `DjangoSnippet 1253 <https://djangosnippets.org/snippets/1253/>`_ by
  `joonas <https://djangosnippets.org/users/joonas/>`_.
   foo_8d989bcc36140573a0f4d5f1e0e1e99e9a90a9f4

  * Updated per `comment 1553 <https://djangosnippets.org/snippets/1253/#c1553>`_
    by `nosa_manuel <https://djangosnippets.org/users/nosa_manuel/>`_.
    foo_ff258ca20f2a5c8e536a744fb9b64fba87046ef5
  * Updated per `comment 4642 <https://djangosnippets.org/snippets/1253/#c4642>`_
    by `esquevin <https://djangosnippets.org/users/esquevin/>`_.
    foo_04b5fe14a5e8803c2b11259ff60c095fb9da8ce3
* `DjangoSnippet 1933 <https://djangosnippets.org/snippets/1933/>`_ by
  `t_rybik <https://djangosnippets.org/users/t_rybik/>`_.
  foo_93f5575b3661bd2334960767eadf4a1ba03bfb8f
* `django-ko-demo from The Atlantic <https://github.com/theatlantic/django-ko-demo/blob/1a37c9ad9bcd68a40c35462fb819fff85a9533f7/apps/curation_nouveau/queryset_sequence.py>`_
  by `@fdintino <https://github.com/fdintino>`_.
  foo_0b875aeb8aaea20ba47fc2fbc285d078aee42240
