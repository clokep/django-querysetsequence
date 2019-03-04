"""
More efficient pagination for django-querysetsequence when using Django REST
Framework.

The standard Django REST Framework pagination classes will work fine. The
classes provided here are useful when providing large datasets that use
QuerySetSequence over an API as they first order by the QuerySet number and then
particular fields.

"""
from base64 import b64decode

from django.utils.six.moves.urllib import parse as urlparse

from queryset_sequence import QuerySetSequence

try:
    from rest_framework.exceptions import NotFound
    from rest_framework.pagination import (_positive_int,
                                           _reverse_ordering,
                                           Cursor,
                                           CursorPagination)
except ImportError:
    # This requires Django REST Framework to be installed.
    raise ImportError(
        "queryset_sequence.pagination is for use with Django REST Framework, "
        "which was not found.")


class SequenceCursorPagination(CursorPagination):
    """
    Heavily customized CursorPagination to first sort by QuerySet, then by a
    different ordering field.

    Changes include:
    * Don't override self.ordering with the output of get_ordering()
    * The filtering logic is significantly changed to deal with a tuple of fields.

    """

    def paginate_queryset(self, queryset, request, view=None):
        # This code only works with a QuerySetSequence.
        if not isinstance(queryset, QuerySetSequence):
            raise ValueError(
                "%s can only be used with an instance of QuerySetSequence." %
                self.__class__.__name__)

        self.page_size = self.get_page_size(request)
        if not self.page_size:
            return None

        self.base_url = request.build_absolute_uri()
        self.ordering = self.get_ordering(request, queryset, view)

        self.cursor = self.decode_cursor(request)
        if self.cursor is None:
            (offset, reverse, current_position) = (0, False, None)
        else:
            (offset, reverse, current_position) = self.cursor

        # Cursor pagination always enforces an ordering.
        if reverse:
            queryset = queryset.order_by(*_reverse_ordering(self.ordering))
        else:
            queryset = queryset.order_by(*self.ordering)

        # If we have a cursor with a fixed position then filter by that.
        if current_position is not None:
            # Iterate over each positioning.
            for order, position in zip(self.ordering[:len(current_position)], current_position):
                # The inside of this loop is essentially the old logic.
                is_reversed = order.startswith('-')
                order_attr = order.lstrip('-')

                # The filtering code in paginate_queryset uses ge or le, so
                # offset these based on that.
                if order_attr == '#':
                    equal = 'e'
                else:
                    equal = ''

                # Test for: (cursor reversed) XOR (queryset reversed)
                if self.cursor.reverse != is_reversed:
                    kwargs = {order_attr + '__lt' + equal: position}
                else:
                    kwargs = {order_attr + '__gt' + equal: position}

                # If filtering on the number of the QuerySet, apply it to the
                # entire QuerySetSequence.
                if order_attr == '#':
                    queryset = queryset.filter(**kwargs)

                # If there *are* QuerySets, filter just the edge QuerySet. This
                # avoids trimming items in subsequent QuerySets that are still
                # valid.
                elif queryset._querysets:
                    queryset = queryset._clone()

                    # Make a copy of the current QuerySets.
                    querysets = queryset._querysets
                    # Handle whether to look at the front edge or back edge of
                    # the QuerySets based on the order of iteration.
                    if self.cursor.reverse != is_reversed:
                        queryset._querysets = (
                            querysets[:-1] +
                            [querysets[-1].filter(**kwargs)])
                    else:
                        queryset._querysets = (
                            [querysets[0].filter(**kwargs)] +
                            querysets[1:])

        # If we have an offset cursor then offset the entire page by that amount.
        # We also always fetch an extra item in order to determine if there is a
        # page following on from this one.
        results = list(queryset[offset:offset + self.page_size + 1])
        self.page = list(results[:self.page_size])

        # Determine the position of the final item following the page.
        if len(results) > len(self.page):
            has_following_position = True
            following_position = self._get_position_from_instance(results[-1], self.ordering)
        else:
            has_following_position = False
            following_position = None

        # If we have a reverse queryset, then the query ordering was in reverse
        # so we need to reverse the items again before returning them to the user.
        if reverse:
            self.page = list(reversed(self.page))

        if reverse:
            # Determine next and previous positions for reverse cursors.
            self.has_next = (current_position is not None) or (offset > 0)
            self.has_previous = has_following_position
            if self.has_next:
                self.next_position = current_position
            if self.has_previous:
                self.previous_position = following_position
        else:
            # Determine next and previous positions for forward cursors.
            self.has_next = has_following_position
            self.has_previous = (current_position is not None) or (offset > 0)
            if self.has_next:
                self.next_position = following_position
            if self.has_previous:
                self.previous_position = current_position

        # Display page controls in the browsable API if there is more
        # than one page.
        if (self.has_previous or self.has_next) and self.template is not None:
            self.display_page_controls = True

        return self.page

    def get_ordering(self, *args, **kwargs):
        """Take whatever the expected ordering is and then first order by QuerySet."""
        result = super(SequenceCursorPagination, self).get_ordering(*args, **kwargs)

        # Because paginate_queryset sets self.ordering after reading it...we
        # need to only modify it sometimes. (This allows re-use of the
        # paginator, which probably only happens in tests.)
        if result[0] != '#':
            result = ('#', ) + result

        return result

    def _get_position_from_instance(self, instance, ordering):
        """
        The position will be a tuple of values:

            The QuerySet number inside of the QuerySetSequence.
            Whatever the normal value taken from the ordering property gives.

        """
        # Get the QuerySet number of the current instance.
        qs_order = getattr(instance, '#')

        # Strip the '#' and call the standard _get_position_from_instance.
        result = super(SequenceCursorPagination, self)._get_position_from_instance(instance, ordering[1:])

        # Return a tuple of these two elements.
        return (qs_order, result)

    def decode_cursor(self, request):
        """
        Given a request with a cursor, return a `Cursor` instance.

        Differs from the standard CursorPagination to handle a tuple in the
        position field.
        """
        # Determine if we have a cursor, and if so then decode it.
        encoded = request.query_params.get(self.cursor_query_param)
        if encoded is None:
            return None

        try:
            querystring = b64decode(encoded.encode('ascii')).decode('ascii')
            tokens = urlparse.parse_qs(querystring, keep_blank_values=True)

            offset = tokens.get('o', ['0'])[0]
            offset = _positive_int(offset, cutoff=self.offset_cutoff)

            reverse = tokens.get('r', ['0'])[0]
            reverse = bool(int(reverse))

            # The difference. Don't get just the 0th entry: get all entries.
            position = tokens.get('p', None)
        except (TypeError, ValueError):
            raise NotFound(self.invalid_cursor_message)

        return Cursor(offset=offset, reverse=reverse, position=position)
