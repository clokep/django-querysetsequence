Example usage
=============

Below is a fuller example of how to use a ``QuerySetSequence``. Two similar, but
not identical models exist (``Article`` and ``Book``):

.. code-block:: python

    class Author(models.Model):
        name = models.CharField(max_length=50)

        class Meta:
            ordering = ['name']

        def __str__(self):
            return self.name


    class Article(models.Model):
        title = models.CharField(max_length=100)
        author = models.ForeignKey(Author)

        def __str__(self):
            return "%s by %s" % (self.title, self.author)


    class Book(models.Model):
        title = models.CharField(max_length=50)
        author = models.ForeignKey(Author)
        release = models.DateField(auto_now_add=True)

        def __str__(self):
            return "%s by %s" % (self.title, self.author)

We'll also want some data to illustrate how ``QuerySetSequence`` works:

.. code-block:: python

    # Create some data.
    alice = Author.objects.create(name='Alice')
    article = Article.objects.create(title='Dancing with Django', author=alice)

    bob = Author.objects.create(name='Bob')
    article = Article.objects.create(title='Django-isms', author=bob)
    article = Book.objects.create(title='Biography', author=bob)

    # Create some QuerySets.
    books = Book.objects.all()
    articles = Article.objects.all()

By wrapping a ``QuerySet`` of each into a ``QuerySetSequence`` they can be treated
as a single ``QuerySet``, for example we can filter to a particular author's work, or
alphabetize all all articles and books together.

.. code-block:: python

    # Combine them into a single iterable.
    published_works = QuerySetSequence(books, articles)

    # Find Bob's titles.
    bob_works = published_works.filter(author=bob)
    # Still an iterable.
    print([w.title for w in bob_works])  # prints: ['Biography', 'Django-isms']

    # Alphabetize the QuerySet.
    published_works = published_works.order_by('title')
    print([w.title for w in published_works])  # prints ['Biography', 'Dancing with Django', 'Django-isms']


Django REST Framework integration
---------------------------------

django-querysetsequence comes with a custom |CursorPagination|_ class that
helps integration with Django REST Framework. It is optimized to iterate over a
``QuerySetSequence`` first by ``QuerySet`` and then by the normal ``ordering``
configuration. This uses the optimized code-path for iteration that avoids
interleaving the individual ``QuerySets``.

To handle exceptions and filtering correctly, a ``model`` must be specified when creating
the ``QuerySetSequence``. Note that an abstract model may be used.

For example:

.. code-block:: python

    from queryset_sequence.pagination import SequenceCursorPagination

    class PublicationPagination(SequenceCursorPagination):
        ordering = ['author', 'title']

    class PublicationViewSet(viewsets.ModelViewSet):
        pagination_class = PublicationPagination

        def get_queryset(self):
            # This will return all Books first, then all Articles. Each of those
            # is individually ordered by ``author``, then ``title``.
            return QuerySetSequence(Book.objects.all(), Article.objects.all(), model=Book)


.. |CursorPagination| replace:: ``CursorPagination``
.. _CursorPagination: https://www.django-rest-framework.org/api-guide/pagination/#cursorpagination
