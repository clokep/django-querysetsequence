from itertools import chain, dropwhile
from operator import mul, attrgetter, __not__

from django.db.models.query import EmptyQuerySet, QuerySet


def multiply_iterables(it1, it2):
    """
    Element-wise iterables multiplications.
    """
    assert len(it1) == len(it2),\
           "Can not element-wise multiply iterables of different length."
    return map(mul, it1, it2)

class QuerySequence(object):
    """
    A Query that handles multiple QuerySets.

    The API is expected to match django.db.models.sql.query.Query.

    """

    def __init__(self, *args):
        self._iterables = args
        self._ordering = ['pk']

        # Below is copied from django.db.models.sql.query.Query.
        self.low_mark, self.high_mark = 0, None

    #####################################################
    # METHODS TO MATCH django.db.models.sql.query.Query #
    #####################################################

    # Must implement:
    # add_annotation
    # add_deferred_loading
    # add_distinct_fields,
    # add_extra
    # add_immediate_loading
    # add_ordering
    # add_q
    # add_select_related
    # add_update_fields
    # annotations
    # clear_deferred_loading
    # clear_ordering
    # clone

    def clone(self, klass=None, memo=None, **kwargs):
        """
        Creates a copy of the current instance. The 'kwargs' parameter can be
        used by clients to update attributes after copying has taken place.
        """
        obj = QuerySequence()

        # Copy important properties.
        obj._iterables = map(lambda it: it._clone(), self._iterables)
        obj._ordering = list(self._ordering)

        obj.__dict__.update(kwargs)
        return obj

    # combine
    # default_ordering
    # distinct_Fields
    # extra_order_by
    # filter_is_sticky
    # get_aggregation
    # get_compiler

    def get_count(self, using):
        """Request count on each sub-query."""
        return sum(map(lambda it: it.count(), self._iterables))

    def set_limits(self, low=None, high=None):
        """
        Adjusts the limits on the rows retrieved. We use low/high to set these,
        as it makes it more Pythonic to read and write. When the SQL query is
        created, they are converted to the appropriate offset and limit values.

        Any limits passed in here are applied relative to the existing
        constraints. So low is added to the current low value and both will be
        clamped to any existing high value.

        Directly copied from django.db.models.sql.query.Query.
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

        Directly copied from django.db.models.sql.query.Query.
        """
        self.low_mark, self.high_mark = 0, None

    def can_filter(self):
        """
        Returns True if adding filters to this instance is still possible.

        Typically, this means no limits or offsets have been put on the results.

        Directly copied from django.db.models.sql.query.Query.
        """
        return not self.low_mark and self.high_mark is None

    # get_meta
    # group_by
    # has_filters
    # has_results
    # insert_values
    # is_empty
    # order_by
    # select_for_update
    # select_for_update_nowait
    # select_related
    # set_empty
    # standard_ordering

    def __iter__(self):
        return self.__generator__()

    def __generator__(self):
        # TODO Error checking.

        # TODO This breaks if there's no ordering.

        # For fields that start with a '-', reverse the ordering of the
        # comparison.
        field_names = self._ordering
        reverses = [-1] * len(field_names)  # Note that this is reverse sorting!
        for i, field_name in enumerate(field_names):
            if field_name[0] == '-':
                reverses[i] = -1 * reverses[i]
                field_names[i] = field_name[1:]

        def fields_getter(i):
            """Returns a tuple of the values to be compared."""
            field_values = attrgetter(*field_names)(i)
            # Always want an tuple, but attrgetter returns single item if 1 arg
            # supplied.
            if len(field_names):
                field_values = (field_values, )
            return field_values

        # Construct a comparator function based on the field names prefixes.
        # comparator gets the first non-zero value of the field comparison
        # results taking into account reverse order for fields prefixed with '-'
        def comparator(i1, i2):
            # Compare each field for the two items, reversing if necessary.
            order = multiply_iterables(map(cmp, fields_getter(i1), fields_getter(i2)), reverses)

            try:
                return dropwhile(__not__, order).next()
            except StopIteration:
                return 0

        # A list of index to items. Prepopulate with the first in each iterable.
        # (Remember that each iterable is already sorted.)
        not_empty_qss = map(iter, filter(None, self._iterables))
        cur_values = enumerate(map(lambda it: next(it), not_empty_qss))

        while cur_values:
            # Sort the current values.
            cur_values = sorted(cur_values, cmp=comparator, key=lambda x: x[1])

            # The 'minimum' value is now in the last position!
            index, value = cur_values.pop()

            # Return this item.
            yield value

            # Pull the next value from the iterable that just lost a value.
            try:
                value = not_empty_qss[index].next()
                cur_values.append((index, value))
            except StopIteration:
                # No new value to add!
                pass


class QuerySetSequence(QuerySet):
    """
    Wrapper for multiple QuerySets without the restriction on the identity of
    the base models.

    """

    def __init__(self, *args, **kwargs):
        if args:
            # TODO If kwargs already has query.
            kwargs['query'] = QuerySequence(*args)

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

        """
        if args or kwargs:
            assert self.query.can_filter(), \
                "Cannot filter a query once a slice has been taken."
        clone = self._clone()

        # Apply the _filter_or_exclude to each QuerySet in the QuerySequence.
        clone.query._iterables = \
            map(lambda qs: qs._filter_or_exclude(negate, *args, **kwargs),
                clone.query._iterables)

        return self._simplify(clone)

    def _simplify(self, qss):
        """
        Returns QuerySetSequence, QuerySet or EmptyQuerySet depending on the
        contents of items, i.e. at least two non empty QuerySets, exactly one
        non empty QuerySet and all empty QuerySets respectively.

        Does not modify original QuerySetSequence.
        """
        not_empty_qss = filter(None, qss.query._iterables)
        if not len(not_empty_qss):
            return EmptyQuerySet()
        if len(not_empty_qss) == 1:
            return not_empty_qss[0]
        return qss

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

    def order_by(self, *field_names):
        """
        Returns a new QuerySetSequence or instance with the ordering changed.
        """
        self._ordering = list(field_names)
        clone = self._clone(lambda qs: qs.order_by(*field_names))
        return clone

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
