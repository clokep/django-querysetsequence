from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50)


class PeriodicalPublisher(models.Model):
    # Stupid distinction, but I need a similar object with a missing field.
    name = models.CharField(max_length=50)


class OnlinePublisher(models.Model):
    # Stupid distinction, but same as PeriodicalPublisher with an ordering.
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ['name']


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    publisher = models.ForeignKey(PeriodicalPublisher, related_name='published', on_delete=models.CASCADE)
    release = models.DateField()

    class Meta:
        get_latest_by = 'release'

    def __str__(self):
        return "%s by %s" % (self.title, self.author)


class BlogPost(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    publisher = models.ForeignKey(OnlinePublisher, related_name='published', on_delete=models.CASCADE)


class Book(models.Model):
    title = models.CharField(max_length=50)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    publisher = models.ForeignKey(Publisher, related_name='published', on_delete=models.CASCADE)
    release = models.DateField()
    pages = models.PositiveSmallIntegerField()

    class Meta:
        get_latest_by = 'release'

    def __str__(self):
        return "%s by %s" % (self.title, self.author)
