from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from queryset_sequence import ProxyModel
from tests.models import Article


class TestProxyModel(TestCase):
    """Tests calls to proxy model are handled as expected"""

    def test_no_model_doesnotexist(self):
        """When no model is defined, generic ObjectDoesNotExist exception is returned"""
        proxy = ProxyModel(model=None)
        self.assertIs(proxy.DoesNotExist, ObjectDoesNotExist)

    def test_model_doesnotexist(self):
        """When a model is defined, model-specific DoesNotExist exception is returned"""
        proxy = ProxyModel(model=Article)
        self.assertIs(proxy.DoesNotExist, Article.DoesNotExist)

    def test_model_meta(self):
        """When a model is defined, model._meta is accessible"""
        proxy = ProxyModel(model=Article)
        self.assertEqual(proxy._meta.model_name, "article")

    def test_no_model_meta(self):
        """When a model is not defined, accessing model meta should fail"""
        proxy = ProxyModel(model=None)
        self.assertRaises(AttributeError, lambda: proxy._meta)

    def test_model_special_methods_are_not_proxied(self):
        """When a model is defined, special methods are not proxied to the model"""
        proxy = ProxyModel(model=Article)
        self.assertIsNot(proxy.__str__, Article.__str__)
