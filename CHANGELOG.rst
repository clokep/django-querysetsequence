.. :changelog:

Changelog
#########

0.12 (2019-12-20)
=================

* [Incompatible change] Drop support for Python 2.7.
* [Incompatible change] Drop support for Django 2.0 and 2.1.
* [Enhancement] Officially support Django 3.0.
* [Enhancement] Officially support Python 3.8.
* [Enhancement] Officially support Django REST Framework 3.10 and 3.11.
* [Bugfix] Do not use ``is not`` to compare to an integer literal.

0.11 (2019-04-25)
=================

* [Enhancement] Add a ``QuerySetSequence`` specific method: ``get_querysets()``.
* [Enhancement] Officially support Django 2.2.
* [Enhancement] Officially support Django REST Framework 3.9.
* [Enhancement] Officially support Python 3.7.
* [Incompatible change] Drop support for Django REST Framework < 3.6.3.
* [Incompatible change] Drop support for Python 3.4.

0.10 (2018-10-09)
=================

* [Enhancement] Support ``first()``, ``last()``, ``latest()``, and
  ``earliest()`` methods.
* [Enhancement] Support the ``&`` and ``|`` operators.
* [Enhancement] Support ``defer()`` and ``only()`` methods to control which
  fields are returned.
* [Enhancement] Support calling ``using()`` to switch databases for an entire
  ``QuerySetSequence``.
* [Enhancement] Support calling ``extra()`, ``update()``, and ``annotate()``
  which get applied to each ``QuerySet``.
* [Enhancement] Support calling ``explain()`` on Django >= 2.1.
* [Bugfix] Raise ``NotImplementedError`` on unimplemented methods. This fixes a
  regression introduced in 0.9.

0.9 (2018-09-20)
================

* [Enhancement] Officially support Django REST Framework 3.7 and 3.8
* [Enhancement] Officially support Django 2.0 and 2.1.
* [Incompatible change] Drop support for Django < 1.11. Django 1.11 and above
  are supported. This also drops support for Django REST Framework < 3.4, since
  they do not support Django 1.11.
* [Bugfix] Stop using the internals of QuerySet for better forward
  compatibility. This change means that ``QuerySetSequence`` is no longer a
  sub-class of ``QuerySet`` and should improve interactions with other packages
  which modify ``QuerySet``.

0.8 (2017-09-05)
================

* [Enhancement] Optimize iteration when *not* slicing a ``QuerySetSequence``.
  See #29.
* [Enhancement] Officially support Django 1.11.
* [Enhancement] Officially support Django REST Framework 3.5 and 3.6.

0.7.2 (2017-04-04)
==================

* [Bugfix] Calling an unimplemented method with parameters on
  ``QuerySetSequence`` raised a non-sensical error.

0.7.1 (2017-03-31)
==================

* [Bugfix] Slicing a ``QuerySetSequence`` did not work properly when the slice
  reduced the ``QuerySetSequence`` to a single ``QuerySet``. See #23, #24.

0.7 (2016-10-20)
================

* [Feature] Allow filtering / querying / ordering by the order of the
  ``QuerySets`` in the ``QuerySetSequence`` by using ``'#'``. This allows for
  additional optimizations when using third-party applications, e.g. Django REST
  Framework.
* [Feature] `Django REST Framework`_ integration: includes a subclass of the
  ``CursorPagination`` from Django REST Framework under
  ``queryset_sequence.pagination.SequenceCursorPagination`` which is designed to
  work efficiently with a ``QuerySetSequence`` by first ordering by internal
  ``QuerySet``, then by the ``ordering`` attribute.
* [Enhancement] Move ``queryset_sequence`` to an actual module in order to hide
  some implementation details.
* [Bugfix] ``PartialInheritanceMeta`` must be provided ``INHERITED_ATTRS`` and
  ``NOT_IMPLEMENTED_ATTRS``.

.. _Django REST Framework: http://www.django-rest-framework.org/

0.6.1 (2016-08-03)
==================

* [Enhancement] Officially support Django 1.10.

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
