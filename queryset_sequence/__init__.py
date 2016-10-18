import functools
from itertools import chain, dropwhile
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


class QuerySequence(six.with_metaclass(PartialInheritanceMeta, Query)):
    """
    A Query that handles multiple QuerySets.

    The API is expected to match django.db.models.sql.query.Query.

    """
    INHERITED_ATTRS = [
        'set_empty',
        'is_empty',
        'set_limits',
        'clear_limits',
        'can_filter',
        'add_select_related',
    ]
    NOT_IMPLEMENTED_ATTRS = [
        'add_annotation',
        'add_deferred_loading',
        'add_distinct_fields',
        'add_extra',
        'add_immediate_loading',
        'add_q',
        'add_update_fields',
        'clear_deferred_loading',
        'combine',
        'get_aggregation',
        'get_compiler',
        'get_meta',
        'has_filters',
    ]

    def __init__(self, *args):
        self._querysets = list(args)
        # Mark each QuerySet's Model with the number of the QuerySet it is.
        for i, qs in enumerate(self._querysets):
            # Generate a Proxy model and then modify that to allow for the same
            # Model to be used in multiple QuerySetSequences at once.
            qs.model = self._get_model(qs.model)
            # Also push this to the Query object since that holds it's own
            # reference to QuerySet.model instead of asking the QuerySet for it.
            qs.query.model = qs.model

            # Actually set the attribute.
            setattr(qs.model, '#', i)

        # Call super to pick up a variety of properties.
        super(QuerySequence, self).__init__(model=None)

    def _get_model(self, model):
        """Create (and return) a proxy model which subclasses the given model."""
        model_meta = getattr(model, 'Meta', object)

        class QuerySequenceModel(model):
            class Meta(model_meta):
                proxy = True
                # Note that we must give an app_label or Django complains, it
                # doesn't seem to get used, however.
                app_label = ('queryset_sequence.%s' % uuid.uuid4()).replace('-', '')

        return QuerySequenceModel

    def __str__(self):
        """Return the class-name and memory location; there's no SQL to show."""
        return object.__str__(self)

    def clone(self, *args, **kwargs):
        obj = super(QuerySequence, self).clone(*args, **kwargs)

        # Clone each QuerySet and copy it to the new object.
        obj._querysets = [it._clone() for it in self._querysets]
        return obj

    def get_count(self, using):
        """Request count on each sub-query."""
        if self.is_empty():
            return 0
        return sum([it.count() for it in self._querysets])

    def has_results(self, using):
        """If any sub-query has a result, this is true."""
        return any([it.exists() for it in self._querysets])

    def add_ordering(self, *ordering):
        """Propagate ordering to each QuerySet and save it for iteration."""
        if ordering:
            self.order_by.extend(ordering)

            # Remove the ordering by QuerySet before trying to order the
            # individual QuerySets.
            if ordering[0].lstrip('-') == '#':
                ordering = ordering[1:]

        self._querysets = [it.order_by(*ordering) for it in self._querysets]

    def clear_ordering(self, force_empty):
        """
        Removes any ordering settings.

        Does not propagate to each QuerySet since their is no appropriate API.
        """
        self.order_by = []

    def add_select_related(self, fields):
        # Don't bother splitting this by field sep, etc.
        self.select_related = fields

    def __iter__(self):
        # If this is explicitly marked as empty or there's no QuerySets, just
        # return an empty iterator.
        if not len(self._querysets) or self.is_empty():
            return iter([])

        # Apply any select related calls.
        if isinstance(self.select_related, (list, tuple)):
            self._querysets = [it.select_related(*self.select_related) for it in self._querysets]

        # Reverse the ordering, if necessary. Apply this to both the individual
        # QuerySets and the ordering of the QuerySets themselves.
        if not self.standard_ordering:
            self._querysets = [it.reverse() for it in self._querysets]
            self._querysets = self._querysets[::-1]

        # If order is necessary, evaluate and start feeding data back.
        if self.order_by:
            # If the first element of order_by is '#', this means first order by
            # QuerySet. If it isn't this, then returned the interleaved
            # iterator.
            if self.order_by[0].lstrip('-') != '#':
                return self._ordered_iterator()

            # Otherwise, order by QuerySet first. Handle reversing the
            # QuerySets, if necessary.
            elif self.order_by[0].startswith('-'):
                self._querysets = self._querysets[::-1]

        # If there is no ordering, or the ordering is specific to each QuerySet,
        # evaluation can be pushed off further.

        # First trim any QuerySets based on the currently set limits!
        counts = [0]
        counts.extend(cumsum([it.count() for it in self._querysets]))

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

        # A mapping of iterable to the current item in that iterable. (Remember
        # that each QuerySet is already sorted.)
        not_empty_qss = [iter(it) for it in self._querysets if it]
        values = {it: next(it) for it in not_empty_qss}

        # The offset of items returned.
        index = 0

        # Create a comparison function based on the requested ordering.
        _comparator = self._generate_comparator(self.order_by)
        def comparator(i1, i2):
            # Actually compare the 2nd element in each tuple, the 1st element is
            # the generator.
            return _comparator(i1[1], i2[1])
        comparator = functools.cmp_to_key(comparator)

        # If in reverse mode, get the last value instead of the first value from
        # ordered_values below.
        if self.standard_ordering:
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
            if self.low_mark <= index:
                yield value
            index += 1
            # We've left the slice of interest, we're done.
            if index == self.high_mark:
                return

            # Iterate the iterable that just lost a value.
            try:
                values[qss] = next(qss)
            except StopIteration:
                # This iterator is done, remove it.
                del values[qss]


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
        app_label = 'queryset_sequence'
        object_name = 'QuerySetSequenceModel'


class QuerySetSequence(six.with_metaclass(PartialInheritanceMeta, QuerySet)):
    """
    Wrapper for multiple QuerySets without the restriction on the identity of
    the base models.

    """
    INHERITED_ATTRS = [
        # Public methods that return QuerySets.
        'filter',
        'exclude',
        'order_by',
        'reverse',
        'none',
        'all',
        'select_related',

        # Public methods that don't return QuerySets.
        'get',
        'count',
        'as_manager',
        'exists',

        # Public introspection attributes.
        'ordered',
        'db',

        # Private methods.
        '_clone',
        '_fetch_all',
        '_merge_sanity_check',
        '_prepare',
    ]
    NOT_IMPLEMENTED_ATTRS = [
        # Public methods that return QuerySets.
        'annotate',
        'distinct',
        'values',
        'values_list',
        'dates',
        'datetimes',
        'extra',
        'defer',
        'only',
        'using',
        'select_for_update',
        'raw',
        # Public methods that don't return QuerySets.
        'latest',
        'earliest',
        'first',
        'last',
        'aggregate',

        # Public methods that don't return QuerySets. These don't make sense in
        # the context of a QuerySetSequence.
        'create',
        'get_or_create',
        'update_or_create',
        'bulk_create',
        'in_bulk',
        'update',
    ]

    def __init__(self, *args, **kwargs):
        # Create the QuerySequence object where most of the magic happens.
        if 'query' not in kwargs:
            kwargs['query'] = QuerySequence(*args)
        elif args:
            raise ValueError(
                "Cannot provide args and a 'query' keyword argument.")

        # If a particular Model class is not provided, just use the generic
        # model class.
        # TODO Dynamically generate the fields available in this model via
        # introspection of the input QuerySets.
        if 'model' not in kwargs:
            kwargs['model'] = QuerySetSequenceModel

        super(QuerySetSequence, self).__init__(**kwargs)

    def iterator(self):
        # Create a clone so that each call re-evaluates the QuerySets.
        return self.query.clone()

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

        # Separate the kwargs into ones that deal with QuerySets (i.e. are
        # handled by QuerySetSequence) and ones that will be passed onto each
        # QuerySet.
        sequence_kwargs = {}
        queryset_kwargs = {}
        for kwarg, value in kwargs.items():
            if kwarg.startswith('#'):
                sequence_kwargs[kwarg] = value
            else:
                queryset_kwargs[kwarg] = value
        clone._filter_or_exclude_querysets(negate, **sequence_kwargs)

        # Apply the _filter_or_exclude to each QuerySet in the QuerySequence.
        querysets = \
            [qs._filter_or_exclude(negate, *args, **queryset_kwargs) for qs in clone.query._querysets]

        clone.query._querysets = querysets
        return clone

    def _filter_or_exclude_querysets(self, negate, **kwargs):
        """
        Similar to _filter_or_exclude, but run over the QuerySets in the
        QuerySetSequence instead of over each QuerySet's fields.

        """
        # Start with all QuerySets.
        querysets = list(range(len(self.query._querysets)))

        # Ensure negate is a boolean.
        negate = bool(negate)

        for kwarg, value in kwargs.items():
            parts = kwarg.split(LOOKUP_SEP)

            # Ensure this is being used to filter QuerySets.
            if parts[0] != '#':
                raise ValueError("Keyword '%s' is not a valid to filter over, "
                                 "it must begin with '#'." % kwarg)

            # Don't allow __ multiple times.
            if len(parts) > 2:
                raise ValueError("Keyword '%s' must not contain multiple "
                                 "lookup seperators." % kwarg)

            # The actual lookup is the second part.
            try:
                lookup = parts[1]
            except IndexError:
                lookup = 'exact'

            # Math operators that all have the same logic.
            LOOKUP_TO_OPERATOR = {
                'exact': eq,
                'iexact': eq,
                'gt': gt,
                'gte': ge,
                'lt': lt,
                'lte': le,
            }
            try:
                operator = LOOKUP_TO_OPERATOR[lookup]

                # These expect integers, this matches the logic in
                # IntegerField.get_prep_value(). (Essentially treat the '#'
                # field as an IntegerField.)
                if value is not None:
                    value = int(value)

                querysets = filter(lambda i: operator(i, value) != negate, querysets)
                continue
            except KeyError:
                # It wasn't one of the above operators, keep trying.
                pass

            # Some of these seem to get handled as bytes.
            if lookup in ('contains', 'icontains'):
                value = six.text_type(value)
                querysets = filter(lambda i: (value in six.text_type(i)) != negate, querysets)

            elif lookup == 'in':
                querysets = filter(lambda i: (i in value) != negate, querysets)

            elif lookup in ('startswith', 'istartswith'):
                value = six.text_type(value)
                querysets = filter(lambda i: six.text_type(i).startswith(value) != negate, querysets)

            elif lookup in ('endswith', 'iendswith'):
                value = six.text_type(value)
                querysets = filter(lambda i: six.text_type(i).endswith(value) != negate, querysets)

            elif lookup == 'range':
                # Inclusive include.
                start, end = value
                querysets = filter(lambda i: (start <= i <= end) != negate, querysets)

            else:
                # Any other field lookup is not supported, e.g. date, year, month,
                # day, week_day, hour, minute, second, isnull, search, regex, and
                # iregex.
                raise ValueError("Unsupported lookup '%s'" % lookup)

            # Keep querysets a list in Python 3.
            querysets = list(querysets)

        # Finally, trim down the actual QuerySets we care about!
        self.query._querysets = [self.query._querysets[i] for i in querysets]

    def delete(self):
        # Propagate delete to each sub-query.
        for qs in self.query._querysets:
            qs.delete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None

    def prefetch_related(self, *lookups):
        # Don't modify self._prefetch_related_lookups, as that will cause
        # issues, but call prefetch_related on underlying QuerySets.
        clone = self._clone()
        clone.query._querysets = [
            qs.prefetch_related(*lookups) for qs in clone.query._querysets]
        return clone
