This class acts as a wrapper around multiple querysets. Use it if you want to
chain multiple QSs together without combining them with | or &. eg., to put
title matches ahead of body matches::

    >>> qs1 = Event.objects.filter(## title matches ##)
    >>> qs2 = Event.objects.filter(## matches in other fields ##)
    >>> qs = MultiQuerySet(qs1, qs2)
    >>> len(qs)
    >>> paginator = Paginator(qs)
    >>> first_ten = qs[:10]

It effectively acts as an immutable, sliceable QuerySet (with only a very
limited subset of the QuerySet api)

Originally from https://www.djangosnippets.org/snippets/1103/
