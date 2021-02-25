Django QuerySetSequence
#######################

.. image:: https://api.travis-ci.com/clokep/django-querysetsequence.svg?branch=main
    :target: https://travis-ci.com/clokep/django-querysetsequence

.. image:: https://readthedocs.org/projects/django-querysetsequence/badge/?version=latest
    :target: https://django-querysetsequence.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://coveralls.io/repos/github/clokep/django-querysetsequence/badge.svg?branch=master
    :target: https://coveralls.io/github/clokep/django-querysetsequence?branch=master

.. include-start

django-querysetsequence adds helpers for treating multiple disparate ``QuerySet``
obejcts as a single ``QuerySet``. This is useful for passing into APIs that only
accepted a single ``QuerySet``.

The ``QuerySetSequence`` wrapper is used to combine multiple ``QuerySet`` instances.


Overview
========

``QuerySetSequence`` aims to provide the same behavior as Django's |QuerySets|_,
but applied across multiple ``QuerySet`` instances.

.. |QuerySets| replace:: ``QuerySets``
.. _QuerySets: https://docs.djangoproject.com/en/dev/ref/models/querysets/

Supported features:

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


Getting Started
===============

Install the package using pip.

.. code-block:: bash

    pip install --upgrade django-querysetsequence


Basic Usage
===========

.. code-block:: python

    # Import QuerySetSequence
    from queryset_sequence import QuerySetSequence

    # Create QuerySets you want to chain.
    from .models import SomeModel, OtherModel

    # Chain them together.
    query = QuerySetSequence(SomeModel.objects.all(), OtherModel.objects.all())

    # Use query as if it were a QuerySet! E.g. in a ListView.


Project Information
===================

django-querysetsequence is released under the ISC license, its documentation lives
on `Read the Docs`_, the code on `GitHub`_, and the latest release on `PyPI`_. It
supports Python 3.6+, Django 2.2+, and is optionally compatible with
`Django REST Framework`_ 3.9+.

.. _Read the Docs: https://django-querysetsequence.readthedocs.io/
.. _GitHub: https://github.com/clokep/django-querysetsequence
.. _PyPI: https://pypi.org/project/django-querysetsequence/
.. _Django REST Framework: http://www.django-rest-framework.org/

Some ways that you can contribute:

* Check for open issues or open a fresh issue to start a discussion around a
  feature idea or a bug.
* Fork the repository on GitHub to start making your changes.
* Write a test which shows that the bug was fixed or that the feature works as
  expected.
* Send a pull request and bug the maintainer until it gets merged and published.
