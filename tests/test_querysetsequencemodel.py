from django.test import TestCase

from queryset_sequence import QuerySetSequenceModel

class QuerySetSequenceModelTests(TestCase):
    model = QuerySetSequenceModel

    def test_app_label(self):
        self.assertEqual(self.model._meta.app_label, 'queryset_sequence')
        self.assertEqual(self.model()._meta.app_label, 'queryset_sequence')

    def test_object_name(self):
        self.assertEqual(self.model._meta.object_name, 'QuerySetSequenceModel')
        self.assertEqual(self.model()._meta.object_name, 'QuerySetSequenceModel')
