from queryset_sequence import QuerySetSequence


MAGIC_METHODS = [
    # Magic methods.
    '__iter__',     # Iteration / container types.
    '__len__',
    '__getitem__',  # Slicing
    # Pickling
    '__setstate__', '__getstate__', '__reduce__',
    '__repr__',
    '__bool__',     # Boolean
    '__nonzero__',
    '__and__',
    '__or__',
    '__deepcopy__', # Deepcopy
]

QUERYSET_ATTRS = [
    # Public methods that return QuerySets.
    'filter',
    'exclude',
    'annotate',
    'order_by',
    'reverse',
    'distinct',
    'values',
    'values_list',
    'dates',
    'datetimes',
    'none',
    'all',
    'select_related',
    'prefetch_related',
    'extra',
    'defer',
    'only',
    'using',
    'select_for_update',
    'raw',

    # Public methods that don't return QuerySets.
    'get',
    'create',
    'get_or_create',
    'update_or_create',
    'bulk_create',
    'count',
    'in_bulk',
    'iterator',
    'latest',
    'earliest',
    'first',
    'last',
    'aggregate',
    'exists',
    'update',
    'delete',
    'as_manager',
]


NOTES = {
    'order_by': "Does not support random ``order_by()`` (e.g. ``order_by('?')``)"
}
CANNOT_IMPL_ATTRS = [
    'create',
    'get_or_create',
    'update_or_create',
    'bulk_create',
    'in_bulk',
    'update',
]
for attr in CANNOT_IMPL_ATTRS:
    NOTES[attr] = "Cannot be implemented in ``QuerySetSequence``."


def main():
    README = 'README.rst'
    with open(README, 'r') as f:
        # Read all the lines into memory.
        data = f.readlines()

    # Find the split point where we're going to start inserting content.
    ind_start = data.index('.. ATTRIBUTES_TABLE_START\n')
    ind_end = data.index('.. ATTRIBUTES_TABLE_END\n')

    with open(README, 'w') as f:
        # Write all the lines up to (and including) the marker.
        for line in data[:ind_start + 1]:
            f.write(line)

        def writeln(s='', indent_level=0):
            f.write('%s%s\n' % (' ' * indent_level * 4, s))

        # Some templates that are used below.
        writeln(".. |check| unicode:: U+2713")
        writeln(".. |xmark| unicode:: U+2717")
        writeln()

        # The table set-up.
        writeln('.. list-table:: ``QuerySet`` API implemented by ``QuerySetSequence``')
        writeln(':widths: 15 10 30', 1)
        writeln(':header-rows: 1', 1)
        writeln()

        # The table itself.
        writeln('* - Method', 1)
        writeln('  - Implemented?', 1)
        writeln('  - Notes', 1)

        for attr in QUERYSET_ATTRS:
            writeln('* - |%s|_' % attr, 1)
            if attr in QuerySetSequence.__metaclass__.NOT_IMPLEMENTED_ATTRS:
                writeln('  - |xmark|', 1)
            else:
                writeln('  - |check|', 1)
            writeln('  - %s' % NOTES.get(attr, ''), 1)
        writeln()

        # Finally, create all the links.
        for attr in QUERYSET_ATTRS:
            writeln('.. |%s| replace:: ``%s()``' % (attr, attr))
            writeln('.. _%s: https://docs.djangoproject.com/en/dev/ref/models/querysets/#%s' %
                    (attr, attr))

        # Write all the lines after the end delimiter.
        for line in data[ind_end:]:
            f.write(line)

if __name__ == '__main__':
    main()
    exit(0)
