"""Shamelessly stolen from https://djangosnippets.org/snippets/1933/"""

from itertools import chain, dropwhile
from operator import mul, attrgetter, __not__

from django.db.models.query import REPR_OUTPUT_SIZE, EmptyQuerySet


def multiply_iterables(it1, it2):
    """
    Element-wise iterables multiplications.
    """
    assert len(it1) == len(it2),\
           "Can not element-wise multiply iterables of different length."
    return map(mul, it1, it2)


class IterableSequence(object):
    """
    Wrapper for sequence of iterable and indexable by non-negative integers
    objects. That is a sequence of objects which implement __iter__, __len__ and
    __getitem__ for slices, ints and longs.

    Note: not a Django-specific class.
    """

    def __init__(self, *args, **kwargs):
        self.iterables = args # wrapped sequence
        self._len = None # length cache
        self._collapsed = [] # collapsed elements cache

    def __len__(self):
        if not self._len:
            self._len = sum(len(iterable) for iterable in self.iterables)
        return self._len

    def __iter__(self):
        return chain(*self.iterables)

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
        it = self.iterables.__iter__()
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

    def __getitem__(self, key):
        """
        Preserves wrapped indexable sequences.
        Does not support negative indices.
        """
        # params validation
        if not isinstance(key, (slice, int, long)):
            raise TypeError
        assert ((not isinstance(key, slice) and (key >= 0))
                or (isinstance(key, slice) and (key.start is None or key.start >= 0)
                    and (key.stop is None or key.stop >= 0))), \
                "Negative indexing is not supported."
        # initialization
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            ret_item = False
        else: # isinstance(key, (int,long))
            start, stop, step = key, key + 1, 1
            ret_item = True
        # collect sub sets
        ret_iterables = self._collect(start, stop, step)
        # return the simplest possible answer
        if not len(ret_iterables):
            if ret_item:
                raise IndexError("'%s' index out of range" % self.__class__.__name__)
            return ()
        if ret_item:
            # we have exactly one query set with exactly one item
            assert len(ret_iterables) == 1 and len(ret_iterables[0]) == 1
            return ret_iterables[0][0]
        # otherwise we have more then one item in at least one query set
        if len(ret_iterables) == 1:
            return ret_iterables[0]
        # Note: this can't be self.__class__ instead of IterableSequence; exemplary
        # cause is that indexing over query sets returns lists so we can not
        # return QuerySetSequence by default. Some type checking enhancement can
        # be implemented in subclasses.
        return IterableSequence(*ret_iterables)

    def collapse(self, stop=None):
        """
        Collapses sequence into a list.

        Try to do it effectively with caching.
        """
        print("COLLAPSING!")
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

    def __repr__(self):
        # get +1 element for the truncation msg if applicable
        items = self.collapse(stop=REPR_OUTPUT_SIZE + 1)
        if len(items) > REPR_OUTPUT_SIZE:
            items[-1] = "...(remaining elements truncated)..."
        return repr(items)


class QuerySetSequence(IterableSequence):
    """
    Wrapper for the query sets sequence without the restriction on the identity
    of the base models.
    """

    def __init__(self, *args, **kwargs):
        super(QuerySetSequence, self).__init__(*args, **kwargs)
        self._ordering = []

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
        not_empty_qss = map(iter, filter(None, self.iterables))
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

    def _clone(self, it_method=None):
        """
        Retruns a new QuerySetSequence, optionally applying a method to each of
        the iterables.
        """
        query = QuerySetSequence(*map(it_method, self.iterables))
        # Copy over important properties.
        query._ordering = self._ordering
        return query

    def all(self):
        return self

    def count(self):
        if not self._len:
            self._len = sum(qs.count() for qs in self.iterables)
        return self._len

    def __len__(self):
        # override: use DB effective count's instead of len()
        return self.count()

    def order_by(self, *field_names):
        """
        Returns a new QuerySetSequence or instance with the ordering changed.
        """
        self._ordering = list(field_names)
        clone = self._clone(lambda qs: qs.order_by(*field_names))
        return clone

    def filter(self, *args, **kwargs):
        """
        Returns a new QuerySetSequence or instance with the args ANDed to the
        existing set.

        QuerySetSequence is simplified thus result actually can be one of:
        QuerySetSequence, QuerySet, EmptyQuerySet.
        """
        return self._filter_or_exclude(False, *args, **kwargs)

    def exclude(self, *args, **kwargs):
        """
        Returns a new QuerySetSequence instance with NOT (args) ANDed to the
        existing set.

        QuerySetSequence is simplified thus result actually can be one of:
        QuerySetSequence, QuerySet, EmptyQuerySet.
        """
        return self._filter_or_exclude(True, *args, **kwargs)

    def _simplify(self):
        """
        Returns QuerySetSequence, QuerySet or EmptyQuerySet depending on the
        contents of items, i.e. at least two non empty QuerySets, exactly one
        non empty QuerySet and all empty QuerySets respectively.

        Does not modify original QuerySetSequence.
        """
        not_empty_qss = filter(None, self.iterables)
        if not len(not_empty_qss):
            return EmptyQuerySet()
        if len(not_empty_qss) == 1:
            return not_empty_qss[0]
        return self

    def _filter_or_exclude(self, negate, *args, **kwargs):
        """
        Maps _filter_or_exclude over QuerySet items and simplifies the result.
        """
        # each QuerySet is cloned separately
        clone = self._clone(lambda qs: qs._filter_or_exclude(negate, *args, **kwargs))
        return self._simplify()

    def exists(self):
        for qs in self.iterables:
            if qs.exists():
                return True
        return False
