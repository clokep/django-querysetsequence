from itertools import chain, dropwhile
from operator import mul, attrgetter, __not__

from django.core.exceptions import (FieldError, MultipleObjectsReturned,
                                    ObjectDoesNotExist)
from django.db.models.base import Model
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query import QuerySet
from django.db.models.sql.query import ORDER_PATTERN

def multiply_iterables(it1, it2):
    """
    Element-wise iterables multiplications.
    """
    assert len(it1) == len(it2),\
           "Can not element-wise multiply iterables of different length."
    return map(mul, it1, it2)


def cumsum(seq):
    s = 0
    for c in seq:
       s += c
       yield s


class QuerySequence(object):
    """
    A Query that handles multiple QuerySets.

    The API is expected to match django.db.models.sql.query.Query.

    """

    def __init__(self, *args):
        self._querysets = list(args)

        # Below is copied from django.db.models.sql.query.Query.
        self.filter_is_sticky = False

        self.order_by = []
        self.low_mark, self.high_mark = 0, None
        self.distinct_fields = []

    #####################################################
    # METHODS TO MATCH django.db.models.sql.query.Query #
    #####################################################

    # Must implement:
    # add_annotation
    # add_deferred_loading
    # add_distinct_fields
    # add_extra
    # add_immediate_loading
    # add_q
    # add_select_related
    # add_update_fields
    # annotations
    # clear_deferred_loading
    # combine
    # default_ordering
    # extra_order_by
    # filter_is_sticky
    # get_aggregation
    # get_compiler
    # get_meta
    # group_by
    # has_filters
    # has_results
    # insert_values
    # select_for_update
    # select_for_update_nowait
    # select_related
    # standard_ordering

    def clone(self, klass=None, memo=None, **kwargs):
        """
        Creates a copy of the current instance. The 'kwargs' parameter can be
        used by clients to update attributes after copying has taken place.
        """
        obj = QuerySequence()

        # Copy important properties.
        obj._querysets = map(lambda it: it._clone(), self._querysets)
        obj.filter_is_sticky = self.filter_is_sticky
        obj.order_by = self.order_by[:]
        obj.low_mark, obj.high_mark = self.low_mark, self.high_mark

        obj.__dict__.update(kwargs)
        return obj

    def get_count(self, using):
        """Request count on each sub-query."""
        return sum(map(lambda it: it.count(), self._querysets))

    def set_empty(self):
        self._querysets = []

    def is_empty(self):
        return bool(len(self._querysets))

    def add_ordering(self, *ordering):
        """
        Propagate ordering to each QuerySet and save it for iteration.
        """
        # TODO Roll-up errors.
        self._querysets = map(lambda it: it.order_by(*ordering), self._querysets)

        if ordering:
            self.order_by.extend(ordering)

    def clear_ordering(self, force_empty):
        """
        Removes any ordering settings.

        Does not propagate to each QuerySet since their is no appropriate API.
        """
        self.order_by = []

    def __iter__(self):
        # There's no QuerySets, just return an empty iterator.
        if not len(self._querysets):
            return iter([])

        # If order is necessary, evaluate and start feeding data back.
        if self.order_by:
            return self._ordered_iterator()

        # If there is no ordering, evaluation can be pushed off further.

        # First trim any QuerySets based on the currently set limits!
        counts = [0]
        counts.extend(cumsum(map(lambda it: it.count(), self._querysets)))

        # TODO Do we need to work with a clone of _querysets?

        # Trim the beginning of the QuerySets, if necessary.
        start_index = 0
        if self.low_mark is not 0:
            # Convert a negative index into a positive.
            if self.low_mark < 0:
                self.low_mark += counts[-1]

            # Find the point when low_mark crosses a threshold.
            for i, offset in enumerate(counts):
                if offset <= self.low_mark:
                    start_index = i
                if self.low_mark < offset:
                    break

        # Trim the end of the QuerySets, if necessary.
        end_index = len(self._querysets)
        if self.high_mark is None:
            # If it was unset (meaning all), set it to the maximum.
            self.high_mark = counts[-1]
        elif self.high_mark:
            # Convert a negative index into a positive.
            if self.high_mark < 0:
                self.high_mark += counts[-1]

            # Find the point when high_mark crosses a threshold.
            for i, offset in enumerate(counts):
                if self.high_mark <= offset:
                    end_index = i
                    break

        # Remove iterables we don't care about.
        self._querysets = self._querysets[start_index:end_index]

        # The low_mark needs the removed QuerySets subtracted from it.
        self.low_mark -= counts[start_index]
        # The high_mark needs the count of all QuerySets before it subtracted
        # from it.
        self.high_mark -= counts[end_index - 1]

        # Apply the offsets to the edge QuerySets.
        self._querysets[0] = self._querysets[0][self.low_mark:]
        self._querysets[-1] = self._querysets[-1][:self.high_mark]

        # Some optimization, if there is only one QuerySet, iterate through it.
        if len(self._querysets) == 1:
            return iter(self._querysets[0])

        # For anything left, just chain the QuerySets together.
        return chain(*self._querysets)

    @classmethod
    def _fields_getter(cls, field_names, item):
        """
        Returns a tuple of the values to be compared.

        Inputs:
            field_names (iterable of strings): The field names to sort on.
            i (item): The item to get the fields from.

        Returns:
            A tuple of the values of each field in field_names.
        """

        # If field_names refers to a field on a different model (using __
        # syntax), break this apart.
        field_names = map(lambda f: (f.split(LOOKUP_SEP, 2) + [''])[:2], field_names)
        # Split this into a list of the field names on the current item and
        # fields on the values returned.
        field_names, next_field_names = zip(*field_names)

        field_values = attrgetter(*field_names)(item)
        # Always want a list, but attrgetter returns single item if 1 arg
        # supplied.
        if len(field_names) == 1:
            field_values = [field_values]
        else:
            field_values = list(field_values)

        # For any field name that referred to a field on a different model,
        # recursively find the field value.
        for i, next_field_name in enumerate(next_field_names):
            # If next_field_name is empty, the field value is correct.
            if next_field_name:
                field_values[i] = cls._fields_getter([next_field_name], field_values[i])

        return field_values

    @classmethod
    def _get_field_names(cls, model):
        """Return a list of field names that are part of a model."""
        return map(lambda f: f.name, model._meta.get_fields())

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

        def comparator(i1, i2):
            # Get the values for comparison.
            v1 = cls._fields_getter(field_names, i1)
            v2 = cls._fields_getter(field_names, i2)
            # Compare each field for the two items, reversing if necessary.
            order = multiply_iterables(map(cls._cmp, v1, v2), reverses)

            try:
                # The first non-zero element.
                return dropwhile(__not__, order).next()
            except StopIteration:
                # Everything was equivalent.
                return 0

        return comparator

    def _ordered_iterator(self):
        """An iterator that takes into account the requested ordering."""

        # A mapping of iterable to the current item in that iterable. (Remember
        # that each QuerySet is already sorted.)
        not_empty_qss = map(iter, filter(None, self._querysets))
        values = {it: it.next() for it in not_empty_qss}

        # The offset of items returned.
        index = 0

        # Create a comparison function based on the requested ordering.
        comparator = self._generate_comparator(self.order_by)

        # Iterate until all the values are gone.
        while values:
            # If there's only one iterator left, don't bother sorting.
            if len(values) > 1:
                # Sort the current values for each iterable.
                ordered_values = sorted(values.items(), cmp=comparator, key=lambda x: x[1])

                # The 'minimum' value is now in the last position!
                qss, value = ordered_values.pop(0)
            else:
                qss, value = values.items()[0]

            # Return it if we're within the slice of interest.
            if self.low_mark <= index:
                yield value
            index += 1
            # We've left the slice of interest, we're done.
            if index == self.high_mark:
                return

            # Iterate the iterable that just lost a value.
            try:
                values[qss] = qss.next()
            except StopIteration:
                # This iterator is done, remove it.
                del values[qss]

    ##########################################################
    # METHODS DIRECTLY FROM django.db.models.sql.query.Query #
    ##########################################################

    def set_limits(self, low=None, high=None):
        """
        Adjusts the limits on the rows retrieved. We use low/high to set these,
        as it makes it more Pythonic to read and write. When the SQL query is
        created, they are converted to the appropriate offset and limit values.

        Any limits passed in here are applied relative to the existing
        constraints. So low is added to the current low value and both will be
        clamped to any existing high value.
        """
        if high is not None:
            if self.high_mark is not None:
                self.high_mark = min(self.high_mark, self.low_mark + high)
            else:
                self.high_mark = self.low_mark + high
        if low is not None:
            if self.high_mark is not None:
                self.low_mark = min(self.high_mark, self.low_mark + low)
            else:
                self.low_mark = self.low_mark + low

    def clear_limits(self):
        """
        Clears any existing limits.
        """
        self.low_mark, self.high_mark = 0, None

    def can_filter(self):
        """
        Returns True if adding filters to this instance is still possible.

        Typically, this means no limits or offsets have been put on the results.
        """
        return not self.low_mark and self.high_mark is None


# TODO Inherit from django.db.models.base.Model.
class QuerySetSequenceModel(object):
    """
    A fake Model that is used to throw DoesNotExist exceptions for
    QuerySetSequence.
    """
    class DoesNotExist(ObjectDoesNotExist):
        pass

    class MultipleObjectsReturned(MultipleObjectsReturned):
        pass

    class _meta:
        object_name = 'QuerySetSequenceModel'


class QuerySetSequence(QuerySet):
    """
    Wrapper for multiple QuerySets without the restriction on the identity of
    the base models.

    """

    def __init__(self, *args, **kwargs):
        if args:
            # TODO If kwargs already has query.
            kwargs['query'] = QuerySequence(*args)
        # A particular model doesn't really make sense, so just use the generic
        # Model class.
        kwargs['model'] = QuerySetSequenceModel

        super(QuerySetSequence, self).__init__(**kwargs)

    def iterator(self):
        return self.query

    ####################################
    # METHODS THAT DO DATABASE QUERIES #
    ####################################

    # TODO

    ##################################################
    # PUBLIC METHODS THAT RETURN A QUERYSET SUBCLASS #
    ##################################################

    # TODO

    ##################################################################
    # PUBLIC METHODS THAT ALTER ATTRIBUTES AND RETURN A NEW QUERYSET #
    ##################################################################

    # def all(self) inherits from QuerySet.
    # def filter(self, *args, **kwargs) inherits from QuerySet.
    # def exclude(self, *args, **kwargs) inherits from QuerySet.

    def _filter_or_exclude(self, negate, *args, **kwargs):
        """
        Maps _filter_or_exclude over QuerySet items and simplifies the result.

        Returns QuerySetSequence, or QuerySet depending on the contents of
        items, i.e. at least two non empty QuerySets, or exactly one non empty
        QuerySet.
        """
        if args or kwargs:
            assert self.query.can_filter(), \
                "Cannot filter a query once a slice has been taken."
        clone = self._clone()

        # Apply the _filter_or_exclude to each QuerySet in the QuerySequence.
        querysets = \
            map(lambda qs: qs._filter_or_exclude(negate, *args, **kwargs),
                clone.query._querysets)

        # Filter out now empty QuerySets.
        querysets = filter(None, querysets)

        # If there's only one QuerySet left, then return it. Otherwise return
        # the clone.
        if len(querysets) == 1:
            return querysets[0]

        clone.query._querysets = querysets
        return clone

    def complex_filter(self, filter_obj):
        raise NotImplementedError("QuerySetSequence does not implement complex_filter()")

    def select_for_update(self, nowait=False):
        raise NotImplementedError("QuerySetSequence does not implement select_for_update()")

    def select_related(self, *fields):
        raise NotImplementedError("QuerySetSequence does not implement select_related()")

    def prefetch_related(self, *lookups):
        raise NotImplementedError("QuerySetSequence does not implement prefetch_related()")

    def annotate(self, *args, **kwargs):
        raise NotImplementedError("QuerySetSequence does not implement annotate()")

    # def order_by(self, *field_names): inherits from QuerySet.

    def distinct(self, *field_names):
        raise NotImplementedError("QuerySetSequence does not implement distinct()")

    def extra(self, select=None, where=None, params=None, tables=None,
              order_by=None, select_params=None):
        raise NotImplementedError("QuerySetSequence does not implement extra()")

    def reverse(self):
        raise NotImplementedError("QuerySetSequence does not implement reverse()")

    def defer(self, *fields):
        raise NotImplementedError("QuerySetSequence does not implement defer()")

    def only(self, *fields):
        raise NotImplementedError("QuerySetSequence does not implement only()")

    def using(self, alias):
        raise NotImplementedError("QuerySetSequence does not implement using()")

    ###################################
    # PUBLIC INTROSPECTION ATTRIBUTES #
    ###################################

    # ordered
    # db

    ###################
    # PRIVATE METHODS #
    ###################

    def _insert(self, objs, fields, return_id=False, raw=False, using=None):
        raise NotImplementedError("QuerySetSequence does not implement _insert()")

    def _batched_insert(self, objs, fields, batch_size):
        raise NotImplementedError("QuerySetSequence does not implement _batched_insert()")

    # def _clone(self): inherits from QuerySet.

    # def _fetch_all(self): inherits from QuerySet.

    def _next_is_sticky(self):
        raise NotImplementedError("QuerySetSequence does not implement _next_is_sticky()")

    # def _merge_sanity_check(self, other): inherits from QuerySet.

    def _merge_known_related_objects(self, other):
        raise NotImplementedError("QuerySetSequence does not implement _merge_known_related_objects()")

    def _setup_aggregate_query(self, aggregates):
        raise NotImplementedError("QuerySetSequence does not implement _setup_aggregate_query()")

    # def _prepare(self): inherits from QuerySet.

    def _as_sql(self, connection):
        raise NotImplementedError("QuerySetSequence does not implement _as_sql()")

    def _add_hints(self, **hints):
        raise NotImplementedError("QuerySetSequence does not implement _add_hints()")

    def _has_filters(self):
        raise NotImplementedError("QuerySetSequence does not implement _has_filters()")

    def is_compatible_query_object_type(self, opts):
        raise NotImplementedError("QuerySetSequence does not implement is_compatible_query_object_type()")
