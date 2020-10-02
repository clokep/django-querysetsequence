from tests.test_querysetsequence import TestBase


class TestValues(TestBase):
    def test_values(self):
        """Ensure the values conversion works as expected."""
        with self.assertNumQueries(2):
            values = list(self.all.values())
        titles = [it['title'] for it in values]
        # Foreign keys are kept as IDs.
        authors = [it['author_id'] for it in values]
        self.assertEqual(titles, self.TITLES_BY_PK)
        self.assertEqual(authors, [2, 2, 1, 1, 2])

    def test_fields(self):
        """Ensure the proper fields are returned."""
        with self.assertNumQueries(2):
            # Note that to ensure we go through most of the QuerySetSequence
            # logic this converts the entire results to a list before getting
            # the first element.
            data = list(self.all.values('title'))[0]
        self.assertEqual(data, {'#': 0, 'title': 'Fiction'})

    def test_foreign_key(self):
        """Calling values for a foreign key should end up with the ID."""
        with self.assertNumQueries(2):
            data = list(self.all.values('author'))[0]
        self.assertEqual(data, {'#': 0, 'author': 2})

    def test_join(self):
        with self.assertNumQueries(2):
            data = list(self.all.values('author__name'))[0]
        self.assertEqual(data, {'#': 0, 'author__name': 'Bob'})

    def test_order_by(self):
        """Ensure that order_by() propagates to QuerySets and iteration."""
        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = [it['title'] for it in self.all.values('title').order_by('title')]
        self.assertEqual(data, sorted(self.TITLES_BY_PK))

    def test_order_by_other_field(self):
        """Ordering by a field that isn't included in the responses should work."""
        with self.assertNumQueries(2):
            values = list(self.all.values('title').order_by('release'))
        data = [it['title'] for it in values]
        # Check the expected ordering.
        self.assertEqual(data, [
            'Some Article',
            'Django Rocks',
            'Alice in Django-land',
            'Fiction',
            'Biography',
        ])

        # Check that only the requested fields are returned.
        self.assertEqual(values[0], {'#': 1, 'title': 'Some Article'})
