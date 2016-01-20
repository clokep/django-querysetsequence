from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Publisher(models.Model):
    name = models.CharField(max_length=50)


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author)
    publisher = models.ForeignKey(Publisher)
    release = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s by %s" % (self.title, self.author)


class Book(models.Model):
    title = models.CharField(max_length=50)
    author = models.ForeignKey(Author)
    publisher = models.ForeignKey(Publisher)
    release = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s by %s" % (self.title, self.author)

