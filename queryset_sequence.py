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


class QuerySetSequence(QuerySet):
    """
    Wrapper for multiple QuerySets without the restriction on the identity of
    the base models.

    """

    def __init__(self, *args, **kwargs):
        # Don't call super, the useful parts are below.
        self._result_cache = None

        # Wrapped sequences.
        self._iterables = args

        # Length and calculate elements caches.
        self._len = None
        self._collapsed = []

        # How to order elements of the QuerySets.
        self._ordering = []

    def __len__(self):
        if not self._len:
            self._len = sum(len(iterable) for iterable in self._iterables)
        return self._len

    def __nonzero__(self):
        try:
            iter(self).next()
        except StopIteration:
            return False
        return True

    def _collect(self, start=0, stop=None, step=1):
        if not stop:
            stop = len(self)
        sub_iterables = []
        # collect sub sets
        it = self._iterables.__iter__()
        try:
            while stop > start:
                i = it.next()
                i_len = len(i)
                if i_len > start:
                    # no problem with 'stop' being too big
                    sub_iterables.append(i[start:stop:step])
                start = max(0, start - i_len)
                stop -= i_len
        except StopIteration:
            pass
        return sub_iterables

    def collapse(self, stop=None):
        """
        Collapses sequence into a list.

        Try to do it effectively with caching.
        """
        if not stop:
            stop = len(self)
        # if we already calculated sufficient collapse then return it
        if len(self._collapsed) >= stop:
            return self._collapsed[:stop]
        # otherwise collapse only the missing part
        items = self._collapsed
        sub_iterables = self._collect(len(self._collapsed), stop)
        for sub_iterable in sub_iterables:
            items += sub_iterable
        # cache new collapsed items
        self._collapsed = items
        return self._collapsed

    def __iter__(self):
        return self.__generator__()

    def __generator__(self, start=None, stop=None, step=1):
        if start is None:
            start = 1
        if stop is None:
            stop = len(self)
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

        # The number of elements handled thus far.
        return_count = 0
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
            if start <= return_count < stop:
                yield value
            elif return_count == stop:
                return
            # Otherwise, skip this value.
            return_count += 1

            # Pull the next value from the iterable that just lost a value.
            try:
                value = not_empty_qss[index].next()
                cur_values.append((index, value))
            except StopIteration:
                # No new value to add!
                pass

    def __getitem__(self, key):
        if not isinstance(key, (slice, int, long)):
            raise TypeError

        # Break down the slice object.
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            ret_item = False
        else: # isinstance(key, (int,long))
            start, stop, step = key, key + 1, 1
            ret_item = True

        return self.__generator__(start, stop, step)

        # Note: this can't be self.__class__ instead of IterableSequence; exemplary
        # cause is that indexing over query sets returns lists so we can not
        # return QuerySetSequence by default. Some type checking enhancement can
        # be implemented in subclasses.
        #return IterableSequence(*ret_iterables)

    def count(self):
        if not self._len:
            self._len = sum(qs.count() for qs in self._iterables)
        return self._len

    def __len__(self):
        # override: use DB effective count's instead of len()
        return self.count()

    ####################################
    # METHODS THAT DO DATABASE QUERIES #
    ####################################

    # TODO

    def exists(self):
        for qs in self._iterables:
            if qs.exists():
                return True
        return False

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
        # each QuerySet is cloned separately
        clone = self._clone(lambda qs: qs._filter_or_exclude(negate, *args, **kwargs))
        return self._simplify()

    def complex_filter(self, filter_obj):
        raise NotImplementedError("QuerySetSequene does not implement complex_filter()")

    def select_for_update(self, nowait=False):
        raise NotImplementedError("QuerySetSequene does not implement select_for_update()")

    def select_related(self, *fields):
        raise NotImplementedError("QuerySetSequene does not implement select_related()")

    def prefetch_related(self, *lookups):
        raise NotImplementedError("QuerySetSequene does not implement prefetch_related()")

    def annotate(self, *args, **kwargs):
        raise NotImplementedError("QuerySetSequene does not implement annotate()")

    def order_by(self, *field_names):
        """
        Returns a new QuerySetSequence or instance with the ordering changed.
        """
        self._ordering = list(field_names)
        clone = self._clone(lambda qs: qs.order_by(*field_names))
        return clone

    def distinct(self, *field_names):
        raise NotImplementedError("QuerySetSequene does not implement distinct()")

    def extra(self, select=None, where=None, params=None, tables=None,
              order_by=None, select_params=None):
        raise NotImplementedError("QuerySetSequene does not implement extra()")

    def reverse(self):
        raise NotImplementedError("QuerySetSequene does not implement reverse()")

    def defer(self, *fields):
        raise NotImplementedError("QuerySetSequene does not implement defer()")

    def only(self, *fields):
        raise NotImplementedError("QuerySetSequene does not implement only()")

    def using(self, alias):
        raise NotImplementedError("QuerySetSequene does not implement using()")

    ###################################
    # PUBLIC INTROSPECTION ATTRIBUTES #
    ###################################

    # ordered
    # db

    ###################
    # PRIVATE METHODS #
    ###################

    def _insert(self, objs, fields, return_id=False, raw=False, using=None):
        raise NotImplementedError("QuerySetSequene does not implement _insert()")

    def _batched_insert(self, objs, fields, batch_size):
        raise NotImplementedError("QuerySetSequene does not implement _batched_insert()")

    def _clone(self, it_method=None):
        """
        Returns a new QuerySetSequence, optionally applying a method to each of
        the iterables.
        """
        query = QuerySetSequence(*map(it_method, self._iterables))
        # Copy over important properties.
        query._ordering = self._ordering
        return query

    def _fetch_all(self):
        raise NotImplementedError("QuerySetSequene does not implement _fetch_all()")

    def _next_is_sticky(self):
        raise NotImplementedError("QuerySetSequene does not implement _next_is_sticky()")

    # def _merge_sanity_check(self, other): inherits from QuerySet.

    def _merge_known_related_objects(self, other):
        raise NotImplementedError("QuerySetSequene does not implement _merge_known_related_objects()")

    def _setup_aggregate_query(self, aggregates):
        raise NotImplementedError("QuerySetSequene does not implement _setup_aggregate_query()")

    # def _prepare(self): inherits from QuerySet.

    def _as_sql(self, connection):
        raise NotImplementedError("QuerySetSequene does not implement _as_sql()")

    def _add_hints(self, **hints):
        raise NotImplementedError("QuerySetSequene does not implement _add_hints()")

    def _has_filters(self):
        raise NotImplementedError("QuerySetSequene does not implement _has_filters()")

    def is_compatible_query_object_type(self, opts):
        raise NotImplementedError("QuerySetSequene does not implement is_compatible_query_object_type()")



    def _simplify(self):
        """
        Returns QuerySetSequence, QuerySet or EmptyQuerySet depending on the
        contents of items, i.e. at least two non empty QuerySets, exactly one
        non empty QuerySet and all empty QuerySets respectively.

        Does not modify original QuerySetSequence.
        """
        not_empty_qss = filter(None, self._iterables)
        if not len(not_empty_qss):
            return EmptyQuerySet()
        if len(not_empty_qss) == 1:
            return not_empty_qss[0]
        return self
