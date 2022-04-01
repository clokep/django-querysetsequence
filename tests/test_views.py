import unittest

from django.test import TestCase

from queryset_sequence import QuerySetSequence
from tests.models import AbtractModel, Author

# In-case someone doesn't have Django REST Framework installed, guard tests.
try:
    from rest_framework import filters, generics, serializers
    from rest_framework.test import APIRequestFactory

    factory = APIRequestFactory()

    class TestSerializer(serializers.Serializer):
        id = serializers.IntegerField()

    class TestRetrieveView(generics.RetrieveAPIView):
        queryset = QuerySetSequence(Author.objects.all(), model=Author)
        serializer_class = TestSerializer
        permission_classes = []

    class TestListView(generics.ListAPIView):
        queryset = QuerySetSequence(Author.objects.all(), model=Author)
        serializer_class = TestSerializer
        permission_classes = []
        filter_backends = [filters.SearchFilter]
        search_fields = ["^name"]

    class AbstractModelTestListView(generics.ListAPIView):
        queryset = QuerySetSequence(Author.objects.all(), model=AbtractModel)
        serializer_class = TestSerializer
        permission_classes = []
        filter_backends = [filters.SearchFilter]
        search_fields = ["^name"]

    class AbstractModelTestRetrieveView(generics.RetrieveAPIView):
        queryset = QuerySetSequence(Author.objects.all(), model=AbtractModel)
        serializer_class = TestSerializer
        permission_classes = []

except ImportError:
    factory = None


@unittest.skipIf(
    not factory, "Must have Django REST Framework installed to run view tests."
)
class TestViews(TestCase):
    def setUp(self):
        Author.objects.create(name="Bob")

    def test_get_object(self):
        """Try to get an object that does not exist (should return 404)."""
        request = factory.get("/")
        response = TestRetrieveView.as_view()(request, pk=2)
        self.assertEqual(response.status_code, 404)

    def test_filter_success(self):
        """Try to filter for an author with name 'bob' (should return)."""
        request = factory.get("/", {"search": "bob"})
        response = TestListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_filter_empty(self):
        """Try to filter for an author with name 'alice' (should be empty)."""
        request = factory.get("/", {"search": "alice"})
        response = TestListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_get_object_abstract_model(self):
        """Try to get an abstract object that does not exist (should return 404)."""
        request = factory.get("/")
        response = AbstractModelTestRetrieveView.as_view()(request, pk=2)
        self.assertEqual(response.status_code, 404)

    def test_filter_success_abstract_model(self):
        """Try to filter for an abstract object with name 'bob' (should return)."""
        request = factory.get("/", {"search": "bob"})
        response = AbstractModelTestListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_filter_empty_abstract_model(self):
        """Try to filter for an abstract object with name 'alice' (should be empty)."""
        request = factory.get("/", {"search": "alice"})
        response = AbstractModelTestListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
