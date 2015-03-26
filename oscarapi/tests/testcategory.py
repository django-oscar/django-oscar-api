from oscarapi.tests.utils import APITest
from django.core.urlresolvers import reverse


class CategoryTest(APITest):
    fixtures = ['category']

    def test_category_list(self):
        "Check if we get a list of categories with the default attributes"
        self.response = self.get('category-list')
        self.response.assertStatusEqual(200)
        # we should have three products
        self.assertEqual(len(self.response.body), 2)
        # default we have 3 fields
        category = self.response.body[0]
        default_fields = [
            'id', 'path', 'depth', 'numchild', 'name', 'description', 'image',
            'slug', 'full_name']
        for field in default_fields:
            self.assertIn(field, category)

    def test_category_detail(self):
        "Check product details"
        self.response = self.get(reverse('category-detail', args=(1,)))
        self.response.assertStatusEqual(200)
        default_fields = [
            'id', 'path', 'depth', 'numchild', 'name', 'description', 'image',
            'slug', 'full_name']
        for field in default_fields:
            self.assertIn(field, self.response.body)
        self.response.assertValueEqual('name', "Clothing")
