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
    author = models.ForeignKey(Author)
    publisher = models.ForeignKey(PeriodicalPublisher)
    release = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s by %s" % (self.title, self.author)


class BlogPost(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author)
    publisher = models.ForeignKey(OnlinePublisher)


class Book(models.Model):
    title = models.CharField(max_length=50)
    author = models.ForeignKey(Author)
    publisher = models.ForeignKey(Publisher)
    release = models.DateTimeField(auto_now_add=True)
    pages = models.PositiveSmallIntegerField()

    def __str__(self):
        return "%s by %s" % (self.title, self.author)
