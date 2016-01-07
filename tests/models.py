from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=50)


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author)


class Book(models.Model):
    title = models.CharField(max_length=50)
    author = models.ForeignKey(Author)
    release = models.DateField(auto_now_add=True)
