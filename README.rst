Exemplary usage:

.. code-block:: python

    class Blog(models.Model):
        name = models.CharField(max_length=100)
        def __unicode__(self):
            return self.name

    class Post(models.Model):
        title = models.CharField(max_length=50)
        blog = models.ForeignKey(Blog)
        def __unicode__(self):
            return self.title
        class Meta:
            abstract=True

    class Article(Post):
        text = models.TextField()

    class Link(Post):
        url = models.URLField()

    blog = Blog(name="Exemplary blog")
    blog.save()
    Article(title="#1", text="Exemplary article 1", blog=blog).save()
    Article(title="#2", text="Exemplary article 2", blog=blog).save()
    Link(title="#3", url="http://exemplary.link.com/", blog=blog).save()

    qs1 = Article.objects.all()
    qs2 = Link.objects.all()
    qsseq = QuerySetSequence(qs1, qs2)

    # those all work also on IableSequence
    len(qsseq)
    len(QuerySetSequence(qs2, qs2))
    qsseq[len(qs1)].title

    # this is QuerySetSequence specific
    qsseq.order_by('blog.name','-title')
    excluded_homo = qsseq.exclude(title__contains="3")
    # homogenic results - returns QuerySet
    type(excluded_homo)
    excluded_hetero = qsseq.exclude(title="#2")
    # heterogenic results - returns QuerySetSequence
    type(excluded_hetero)
    excluded_hetero.exists()

You can implement more ``QuerySet`` API methods if needed. If full API is
implemented it makes sense to also subclass the ``QuerySet`` class.

Sources:

* Originally from https://www.djangosnippets.org/snippets/1103/
* Modified version from https://djangosnippets.org/snippets/1253/
* Upgraded version from https://djangosnippets.org/snippets/1933/
