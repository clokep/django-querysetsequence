from __future__ import unicode_literals

from collections import defaultdict
import functools
from itertools import chain, dropwhile, imap
from operator import __not__, attrgetter, eq, ge, gt, le, lt, mul
import uuid

from django.core.exceptions import (FieldError, MultipleObjectsReturned,
                                    ObjectDoesNotExist)
from django.db.models.base import Model
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query import QuerySet
from django.db.models.sql.query import Query
from django.utils import six

from queryset_sequence._inheritance import PartialInheritanceMeta

# Only export the public API for QuerySetSequence. (Note that QuerySequence and
# QuerySetSequenceModel are considered semi-public: the APIs probably won't
# change, but implementation is not guaranteed. Other functions/classes are
# considered implementation details.)
__all__ = ['QuerySetSequence']


def cmp(a, b):
    """Python 2 & 3 version of cmp built-in."""
    return (a > b) - (a < b)


def multiply_iterables(it1, it2):
    """
    Element-wise iterables multiplications.
    """
    assert len(it1) == len(it2),\
        "Can not element-wise multiply iterables of different length."
    return list(map(mul, it1, it2))


def cumsum(seq):
    s = 0
    for c in seq:
        s += c
        yield s


class QuerySequenceIterable(object):
    def __init__(self, querysets, order_by, standard_ordering, low_mark, high_mark):
        # Create a clone so that subsequent calls to iterate are kept separate.
        self._querysets = querysets
        self._order_by = order_by
        self._standard_ordering = standard_ordering
        self._low_mark = low_mark
        self._high_mark = high_mark

    @classmethod
    def _get_field_names(cls, model):
        """Return a list of field names that are part of a model."""
        return [f.name for f in model._meta.get_fields()]

    @classmethod
    def _cmp(cls, value1, value2):
        """
        Comparison method that takes into account Django's special rules when
        ordering by a field that is a model:

            1. Try following the default ordering on the related model.
            2. Order by the model's primary key, if there is no Meta.ordering.

        """
        if isinstance(value1, Model) and isinstance(value2, Model):
            field_names = value1._meta.ordering

            # Assert that the ordering is the same between different models.
            if field_names != value2._meta.ordering:
                valid_field_names = (set(cls._get_field_names(value1)) &
                                     set(cls._get_field_names(value2)))
                raise FieldError(
                    "Ordering differs between models. Choices are: %s" %
                    ', '.join(valid_field_names))

            # By default, order by the pk.
            if not field_names:
                field_names = ['pk']

            # TODO Figure out if we don't need to generate this comparator every
            # time.
            return cls._generate_comparator(field_names)(value1, value2)

        return cmp(value1, value2)

    @classmethod
    def _generate_comparator(cls, field_names):
        """
        Construct a comparator function based on the field names. The comparator
        returns the first non-zero comparison value.

        Inputs:
            field_names (iterable of strings): The field names to sort on.

        Returns:
            A comparator function.
        """

        # For fields that start with a '-', reverse the ordering of the
        # comparison.
        reverses = [1] * len(field_names)
        for i, field_name in enumerate(field_names):
            if field_name[0] == '-':
                reverses[i] = -1
                field_names[i] = field_name[1:]

        field_names = [f.replace(LOOKUP_SEP, '.') for f in field_names]

        def comparator(i1, i2):
            # Get a tuple of values for comparison.
            v1 = attrgetter(*field_names)(i1)
            v2 = attrgetter(*field_names)(i2)

            # If there's only one arg supplied, attrgetter returns a single
            # item, directly return the result in this case.
            if len(field_names) == 1:
                return cls._cmp(v1, v2) * reverses[0]

            # Compare each field for the two items, reversing if necessary.
            order = multiply_iterables(list(map(cls._cmp, v1, v2)), reverses)

            try:
                # The first non-zero element.
                return next(dropwhile(__not__, order))
            except StopIteration:
                # Everything was equivalent.
                return 0

        return comparator

    def _ordered_iterator(self):
        """An iterator that takes into account the requested ordering."""
        querysets = self._querysets

        # A mapping of iterable to the current item in that iterable. (Remember
        # that each QuerySet is already sorted.)
        not_empty_qss = [iter(it) for it in querysets if it]
        values = {it: next(it) for it in not_empty_qss}

        # The offset of items returned.
        index = 0

        # Create a comparison function based on the requested ordering.
        _comparator = self._generate_comparator(self._order_by)
        def comparator(i1, i2):
            # Actually compare the 2nd element in each tuple, the 1st element is
            # the generator.
            return _comparator(i1[1], i2[1])
        comparator = functools.cmp_to_key(comparator)

        # If in reverse mode, get the last value instead of the first value from
        # ordered_values below.
        if self._standard_ordering:
            next_value_ind = 0
        else:
            next_value_ind = -1

        # Iterate until all the values are gone.
        while values:
            # If there's only one iterator left, don't bother sorting.
            if len(values) > 1:
                # Sort the current values for each iterable.
                ordered_values = sorted(values.items(), key=comparator)

                # The next ordering item is in the first position, unless we're
                # in reverse mode.
                qss, value = ordered_values.pop(next_value_ind)
            else:
                qss, value = list(values.items())[0]

            # Return it if we're within the slice of interest.
            if self._low_mark <= index:
                yield value
            index += 1
            # We've left the slice of interest, we're done.
            if index == self._high_mark:
                return

            # Iterate the iterable that just lost a value.
            try:
                values[qss] = next(qss)
            except StopIteration:
                # This iterator is done, remove it.
                del values[qss]

    def __iter__(self):
        # Pull out the attributes we care about.
        querysets = self._querysets

        # If there's no QuerySets, just return an empty iterator.
        if not len(querysets):
            return iter([])

        # If order is necessary, evaluate and start feeding data back.
        if self._order_by:
            # If the first element of order_by is '#', this means first order by
            # QuerySet. If it isn't this, then returned the interleaved
            # iterator.
            if self._order_by[0].lstrip('-') != '#':
                return self._ordered_iterator()

            # Otherwise, order by QuerySet first. Handle reversing the
            # QuerySets, if necessary.
            elif self._order_by[0].startswith('-'):
                querysets = querysets[::-1]

        # If there is no ordering, or the ordering is specific to each QuerySet,
        # evaluation can be pushed off further.
        return chain(*querysets)

        # Some optimization, if there is no slicing, iterate through querysets.
        if query.low_mark == 0 and query.high_mark is None:
            return chain(*querysets)

        # First trim any QuerySets based on the currently set limits!
        counts = [0]
        counts.extend(cumsum([it.count() for it in querysets]))

        # Trim the beginning of the QuerySets, if necessary.
        start_index = 0
        low_mark, high_mark = self._low_mark, self._high_mark
        if low_mark is not 0:
            # Convert a negative index into a positive.
            if low_mark < 0:
                low_mark += counts[-1]

            # Find the point when low_mark crosses a threshold.
            for i, offset in enumerate(counts):
                if offset <= low_mark:
                    start_index = i
                if low_mark < offset:
                    break

        # Trim the end of the QuerySets, if necessary.
        end_index = len(querysets)
        if high_mark is None:
            # If it was unset (meaning all), set it to the maximum.
            high_mark = counts[-1]
        elif high_mark:
            # Convert a negative index into a positive.
            if high_mark < 0:
                high_mark += counts[-1]

            # Find the point when high_mark crosses a threshold.
            for i, offset in enumerate(counts):
                if high_mark <= offset:
                    end_index = i
                    break

        # Remove QuerySets we don't care about.
        querysets = querysets[start_index:end_index]

        # The low_mark needs the removed QuerySets subtracted from it.
        low_mark -= counts[start_index]
        # The high_mark needs the count of all QuerySets before it subtracted
        # from it.
        high_mark -= counts[end_index - 1]

        # Some optimization, if there is only one QuerySet, iterate through it.
        if len(querysets) == 1:
            return iter(querysets[0][low_mark:high_mark])

        # Apply the offsets to the edge QuerySets.
        querysets[0] = querysets[0][low_mark:]
        querysets[-1] = querysets[-1][:high_mark]

        # For anything left, just chain the QuerySets together.
        return chain(*querysets)


class QuerySetSequence(object):
    """
    Wrapper for multiple QuerySets without the restriction on the identity of
    the base models.

    """

    def __init__(self, *args):
        self._querysets = args
        # Some information necessary for properly iterating through a QuerySet.
        self._order_by = []
        self._standard_ordering = True
        self._low_mark, self._high_mark = 0, None

    def _clone(self):
        clone = QuerySetSequence(*[qs._clone() for qs in self._querysets])
        clone._order_by = self._order_by
        clone._standard_ordering = self._standard_ordering
        clone._low_mark = self._low_mark
        clone._high_mark = self._high_mark

        return clone

    def __len__(self):
        # Call len() on each QuerySet to properly cache results.
        return sum(map(len, self._querysets))

    def __iter__(self):
        return iter(QuerySequenceIterable(self._querysets, self._order_by, self._standard_ordering, self._low_mark, self._high_mark))

    def __bool__(self):
        return any(imap(bool, self._querysets))

    def __nonzero__(self):      # Python 2 compatibility
        return type(self).__bool__(self)

    # Methods that return new QuerySets
    def filter(self, **kwargs):
        clone = self._clone()
        clone._querysets = [qs.filter(**kwargs) for qs in self._querysets]
        return clone

    def exclude(self, **kwargs):
        clone = self._clone()
        clone._querysets = [qs.exclude(**kwargs) for qs in self._querysets]
        return clone

    def order_by(self, *fields):
        clone = self._clone()
        clone._querysets = [qs.order_by(*fields) for qs in self._querysets]
        clone._order_by = list(fields)
        return clone

    def reverse(self):
        clone = self._clone()
        clone._querysets = [qs.reverse() for qs in reversed(self._querysets)]
        clone._standard_ordering = not self._standard_ordering
        return clone

    def none(self):
        pass

    def all(self):
        clone = self._clone()
        clone._querysets = [qs.all() for qs in self._querysets]
        return clone

    def select_related(self):
        pass

    def prefetch_related(self):
        pass

    # Methods that do not return QuerySets
    def get(self):
        pass

    def count(self):
        return sum(qs.count() for qs in self._querysets)

    def iterator(self):
        pass

    def exists(self):
        return any(qs.exists() for qs in self._querysets)

    def delete(self):
        deleted_count = 0
        deleted_objects = defaultdict(int)
        for qs in self._querysets:
            # Delete this QuerySet.
            current_deleted_count, current_deleted_objects = qs.delete()

            # Combine the results.
            deleted_count += current_deleted_count
            for obj, count in current_deleted_objects.items():
                deleted_objects[obj] += count

        return deleted_count, dict(deleted_objects)

    def as_manager(self):
        pass

    # Public attributes
    @property
    def ordered(self):
        """
        Returns True if the QuerySet is ordered -- i.e. has an order_by()
        clause.
        """
        return bool(self._order_by)
