from oscarapi.tests.utils import APITest
from django.core.urlresolvers import reverse


class ProductTest(APITest):
    fixtures = [
        'product', 'productcategory', 'productattribute', 'productclass',
        'productattributevalue', 'category', 'attributeoptiongroup',
        'attributeoption', 'stockrecord', 'partner'
    ]

    def test_product_list(self):
        "Check if we get a list of products with the default attributes"
        self.response = self.get('product-list')
        self.response.assertStatusEqual(200)
        # we should have two products
        self.assertEqual(len(self.response.body), 2)
        # default we have 3 fields
        product = self.response.body[0]
        default_fields = ['id', 'url']
        for field in default_fields:
            self.assertIn(field, product)

    def test_product_detail(self):
        "Check product details"
        self.response = self.get(reverse('product-detail', args=(1,)))
        self.response.assertStatusEqual(200)
        default_fields = ['stockrecords', 'description', 'title', 'url',
                          'date_updated', 'recommended_products', 'attributes',
                          'date_created', 'id', 'price', 'availability']
        for field in default_fields:
            self.assertIn(field, self.response.body)
        self.response.assertValueEqual('title', "Oscar T-shirt")

    def test_product_price(self):
        "See if we get the price information"
        self.response = self.get(reverse('product-price', args=(1,)))
        self.response.assertStatusEqual(200)
        self.assertIn('excl_tax', self.response.body)

    def test_product_availability(self):
        "See if we get the availability information"
        self.response = self.get(reverse('product-availability', args=(1,)))
        self.response.assertStatusEqual(200)
        self.assertIn('num_available', self.response.body)
