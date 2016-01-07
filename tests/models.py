from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=50)

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

