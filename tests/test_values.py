import datetime

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
        self.assertCountEqual(values[0].keys(), ['#', 'id', 'author_id', 'pages', 'release', 'title'])

    def test_fields(self):
        """Ensure the proper fields are returned."""
        with self.assertNumQueries(2):
            # Note that to ensure we go through most of the QuerySetSequence
            # logic this converts the entire results to a list before getting
            # the first element.
            data = list(self.all.values('title'))[0]
        self.assertEqual(data, {'title': 'Fiction'})

    def test_foreign_key(self):
        """Calling values for a foreign key should end up with the ID."""
        with self.assertNumQueries(2):
            data = list(self.all.values('author'))[0]
        self.assertEqual(data, {'author': 2})

    def test_join(self):
        """Including a field across a foreign key join should work."""
        with self.assertNumQueries(2):
            data = list(self.all.values('author__name'))[0]
        self.assertEqual(data, {'author__name': 'Bob'})

    def test_qss_field(self):
        """Should be able to include the ordering of the QuerySet in the returned fields."""
        with self.assertNumQueries(2):
            data = list(self.all.values('#', 'author__name'))[0]
        self.assertEqual(data, {'#': 0, 'author__name': 'Bob'})

    def test_order_by(self):
        """Ensure that order_by() propagates to QuerySets and iteration."""
        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = [it['title'] for it in self.all.values('title').order_by('title')]
        self.assertEqual(data, sorted(self.TITLES_BY_PK))

        with self.assertNumQueries(2):
            data = [it['title'] for it in self.all.values('title').order_by('-title')]
        self.assertEqual(data, sorted(self.TITLES_BY_PK, reverse=True))

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
        self.assertEqual(values[0], {'title': 'Some Article'})

    def test_order_by_qs(self):
        """Ordering by a QuerySet should work."""
        with self.assertNumQueries(2):
            values = list(self.all.values('title').order_by('author', '#'))
        data = [it['title'] for it in values]
        # Check the expected ordering.
        self.assertEqual(data, [
            'Django Rocks',
            'Alice in Django-land',
            'Fiction',
            'Biography',
            'Some Article',
        ])

        # Check that only the requested fields are returned.
        self.assertEqual(values[0], {'title': 'Django Rocks'})


class TestValuesList(TestBase):
    def test_values_list(self):
        """Ensure the values conversion works as expected."""
        with self.assertNumQueries(2):
            values = list(self.all.values_list())
        self.assertEqual(values[0], (1, 'Fiction', 2, datetime.date(2001, 6, 12), 10))

    def test_fields(self):
        """Ensure the proper fields are returned."""
        with self.assertNumQueries(2):
            # Note that to ensure we go through most of the QuerySetSequence
            # logic this converts the entire results to a list before getting
            # the first element.
            data = list(self.all.values_list('title'))[0]
        self.assertEqual(data, ('Fiction', ))

    def test_foreign_key(self):
        """Calling values for a foreign key should end up with the ID."""
        with self.assertNumQueries(2):
            data = list(self.all.values_list('author'))[0]
        self.assertEqual(data, (2, ))

    def test_join(self):
        with self.assertNumQueries(2):
            data = list(self.all.values_list('author__name'))[0]
        self.assertEqual(data, ('Bob', ))

    def test_qss_field(self):
        """Should be able to include the ordering of the QuerySet in the returned fields."""
        with self.assertNumQueries(2):
            data = list(self.all.values_list('#', 'author__name'))[0]
        self.assertEqual(data, (0, 'Bob'))

    def test_order_by(self):
        """Ensure that order_by() propagates to QuerySets and iteration."""
        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = [it[0] for it in self.all.values_list('title').order_by('title')]
        self.assertEqual(data, sorted(self.TITLES_BY_PK))

        with self.assertNumQueries(2):
            data = [it[0] for it in self.all.values_list('title').order_by('-title')]
        self.assertEqual(data, sorted(self.TITLES_BY_PK, reverse=True))

    def test_order_by_other_field(self):
        """Ordering by a field that isn't included in the responses should work."""
        with self.assertNumQueries(2):
            values = list(self.all.values_list('title').order_by('release'))
        titles = [it[0] for it in values]
        # Check the expected ordering.
        self.assertEqual(titles, [
            'Some Article',
            'Django Rocks',
            'Alice in Django-land',
            'Fiction',
            'Biography',
        ])
        # Check that only the requested fields are returned.
        self.assertEqual(values[0], ('Some Article', ))

    def test_order_by_qs(self):
        """Ordering by a QuerySet should work."""
        with self.assertNumQueries(2):
            values = list(self.all.values_list('title').order_by('author', '#'))
        data = [it[0] for it in values]
        # Check the expected ordering.
        self.assertEqual(data, [
            'Django Rocks',
            'Alice in Django-land',
            'Fiction',
            'Biography',
            'Some Article',
        ])
        # Check that only the requested fields are returned.
        self.assertEqual(values[0], ('Django Rocks', ))


class TestFlatValuesList(TestBase):
    def test_values_list(self):
        """Ensure the values conversion works as expected."""
        with self.assertNumQueries(2):
            values = list(self.all.values_list(flat=True))
        self.assertEqual(values[0], 1)

    def test_fields(self):
        """Ensure the proper fields are returned."""
        with self.assertNumQueries(2):
            titles = list(self.all.values_list('title', flat=True))
        self.assertEqual(titles, self.TITLES_BY_PK)

    def test_foreign_key(self):
        """Calling values for a foreign key should end up with the ID."""
        with self.assertNumQueries(2):
            data = list(self.all.values_list('author', flat=True))[0]
        self.assertEqual(data, 2)

    def test_join(self):
        with self.assertNumQueries(2):
            data = list(self.all.values_list('author__name', flat=True))[0]
        self.assertEqual(data, 'Bob')

    def test_qss_field(self):
        """Should be able to include the ordering of the QuerySet in the returned fields."""
        with self.assertNumQueries(2):
            data = list(self.all.values_list('#', flat=True))[0]
        self.assertEqual(data, 0)

    def test_order_by(self):
        """Ensure that order_by() propagates to QuerySets and iteration."""
        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = list(self.all.values_list('title', flat=True).order_by('title'))
        self.assertEqual(data, sorted(self.TITLES_BY_PK))

        with self.assertNumQueries(2):
            data = list(self.all.values_list('title', flat=True).order_by('-title'))
        self.assertEqual(data, sorted(self.TITLES_BY_PK, reverse=True))

    def test_order_by_other_field(self):
        """Ordering by a field that isn't included in the responses should work."""
        with self.assertNumQueries(2):
            titles = list(self.all.values_list('title', flat=True).order_by('release'))
        # Check the expected ordering.
        self.assertEqual(titles, [
            'Some Article',
            'Django Rocks',
            'Alice in Django-land',
            'Fiction',
            'Biography',
        ])
        # Check that only the requested fields are returned.
        self.assertEqual(titles[0], 'Some Article')

    def test_order_by_qs(self):
        """Ordering by a QuerySet should work."""
        with self.assertNumQueries(2):
            data = list(self.all.values_list('title', flat=True).order_by('author', '#'))
        # Check the expected ordering.
        self.assertEqual(data, [
            'Django Rocks',
            'Alice in Django-land',
            'Fiction',
            'Biography',
            'Some Article',
        ])


class TestNamedValuesList(TestBase):
    def test_values_list(self):
        """Ensure the values conversion works as expected."""
        with self.assertNumQueries(2):
            values = list(self.all.values_list(named=True))
        self.assertEqual(values[0], (1, 'Fiction', 2, datetime.date(2001, 6, 12), 10))
        self.assertEqual(values[0]._fields, ('id', 'title', 'author_id', 'release', 'pages'))
        # Also check one of the other types.
        self.assertEqual(values[2]._fields, ('id', 'title', 'author_id', 'publisher_id', 'release'))

    def test_fields(self):
        """Ensure the proper fields are returned."""
        with self.assertNumQueries(2):
            values = list(self.all.values_list('title', named=True))
        self.assertEqual([value.title for value in values], self.TITLES_BY_PK)
        # There should only be a single field.
        self.assertEqual(values[0]._fields, ('title',))

    def test_foreign_key(self):
        """Calling values for a foreign key should end up with the ID."""
        with self.assertNumQueries(2):
            data = list(self.all.values_list('author', named=True))[0]
        self.assertEqual(data, (2,))

    def test_join(self):
        with self.assertNumQueries(2):
            data = list(self.all.values_list('author__name', named=True))[0]
        self.assertEqual(data, ('Bob',))

    def test_qss_field(self):
        """Should be able to include the ordering of the QuerySet in the returned fields."""
        with self.assertNumQueries(2):
            data = list(self.all.values_list('#', 'author__name', named=True))[0]
        self.assertEqual(data, (0, 'Bob'))

    def test_order_by(self):
        """Ensure that order_by() propagates to QuerySets and iteration."""
        # Check the titles are properly ordered.
        with self.assertNumQueries(2):
            data = [it[0] for it in self.all.values_list('title', named=True).order_by('title')]
        self.assertEqual(data, sorted(self.TITLES_BY_PK))

        with self.assertNumQueries(2):
            data = [it[0] for it in self.all.values_list('title', named=True).order_by('-title')]
        self.assertEqual(data, sorted(self.TITLES_BY_PK, reverse=True))

    def test_order_by_other_field(self):
        """Ordering by a field that isn't included in the responses should work."""
        with self.assertNumQueries(2):
            values = list(self.all.values_list('title', named=True).order_by('release'))
        titles = [it[0] for it in values]
        # Check the expected ordering.
        self.assertEqual(titles, [
            'Some Article',
            'Django Rocks',
            'Alice in Django-land',
            'Fiction',
            'Biography',
        ])
        # Check that only the requested fields are returned.
        self.assertEqual(values[0], ('Some Article', ))

    def test_order_by_qs(self):
        """Ordering by a QuerySet should work."""
        with self.assertNumQueries(2):
            values = list(self.all.values_list('title', named=True).order_by('author', '#'))
        data = [it[0] for it in values]
        # Check the expected ordering.
        self.assertEqual(data, [
            'Django Rocks',
            'Alice in Django-land',
            'Fiction',
            'Biography',
            'Some Article',
        ])
        # Check that only the requested fields are returned.
        self.assertEqual(values[0], ('Django Rocks',))
