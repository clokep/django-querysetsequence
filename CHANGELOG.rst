.. :changelog:

Changelog
#########

0.6 (2016-06-07)
================

* [Feature] Allow specifying the ``Model`` to use when instantiating a
  ``QuerySetSequence``. This is required for compatibility with some third-party
  applications that check the ``model`` field for equality, e.g. when using the
  ``DjangoFilterBackend`` with Django REST Framework. Thanks @CountZachula #6
* [Feature] Support ``prefetch_related``.
* [Bugfix] Fixes an issue when using Django Debug Toolbar, #8.

0.5 (2016-02-21)
================

* [Enhancement] Significant performance improvements when ordering the
  ``QuerySetSequence``. #5
* [Feature] Support ``delete()`` to remove items.

0.4 (2016-02-03)
================

* [Enhancement] Python 3.4/3.5 support. Thanks @jpic #3

0.3 (2016-01-29)
================

* [Enhancement] Raises ``NotImplementedError`` for ``QuerySet`` methods that
  ``QuerySetSequence`` does not implement.
* [Feature] Support ``reverse()`` to reverse the item ordering
* [Feature] Support ``none()`` to return an ``EmptyQuerySet``
* [Feature] Support ``exists()`` to check if a ``QuerySetSequence`` has any
  results.
* [Feature] Support ``select_related`` to follow foreign-key relationships when
  generating results.
* [Bugfix] Do not evaluate any ``QuerySets`` when calling ``filter()`` or
  ``exclude()`` like a Django ``QuerySet``. Thanks @jpic #1
* [Bugfix] Do not cache the results when calling ``iterator()``.

0.2.4 (2016-01-21)
==================

* Add support for Django 1.9.1
* Support ``order_by()`` that references a related model (e.g. a ``ForeignKey``
  relationship using ``foo`` or ``foo_id`` syntaxes)
* Support ``order_by()`` that references a field on a related model (e.g.
  ``foo__bar``)

0.2.3 (2016-01-11)
==================

* Fixed calling ``order_by()`` with a single field

0.2.2 (2016-01-08)
==================

* Support the ``get()`` method on ``QuerySetSequence``

0.2.1 (2016-01-08)
==================

* Fixed a bug when there's no data to iterate.

0.2 (2016-01-08)
================

* Fixed packaging for pypi
* Do not try to instantiate ``EmptyQuerySet``

0.1 (2016-01-07)
================

* Initial release to support Django 1.8.8
