from six import string_types

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
        # we should have four products
        self.assertEqual(len(self.response.body), 4)
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

    def test_product_attribute_entity(self):
        "Entity attribute tyoe should be supported by means of json method"
        self.response = self.get(reverse('product-detail', args=(4,)))
        self.response.assertStatusEqual(200)

        self.response.assertValueEqual('title', "Entity product")

        attributes = self.response.json()['attributes']
        attributes_by_name = {a['name']:a['value'] for a in attributes}

        self.assertIsInstance(attributes_by_name['entity'], string_types)
        self.assertEqual(attributes_by_name['entity'], "<User: admin> has no json method, can not convert to json")

    def test_product_attributes(self):
        "All oscar attribute types should be supported except entity"
        self.response = self.get(reverse('product-detail', args=(3,)))
        self.response.assertStatusEqual(200)

        self.response.assertValueEqual('title', "lots of attributes")

        attributes = self.response.json()['attributes']
        attributes_by_name = {a['name']:a['value'] for a in attributes}

        # check all the attributes and their types.
        self.assertIsInstance(attributes_by_name['boolean'], bool)
        self.assertEqual(attributes_by_name['boolean'], True)
        self.assertIsInstance(attributes_by_name['date'], string_types)
        self.assertEqual(attributes_by_name['date'], "2018-01-02")
        self.assertIsInstance(attributes_by_name['datetime'], string_types)
        self.assertEqual(attributes_by_name['datetime'], "2018-01-02T10:45:00Z")
        self.assertIsInstance(attributes_by_name['file'], string_types)
        self.assertEqual(attributes_by_name['file'], '/media/images/products/2018/01/sony-xa50ES.pdf')
        self.assertIsInstance(attributes_by_name['float'], float)
        self.assertEqual(attributes_by_name['float'], 3.2)
        self.assertIsInstance(attributes_by_name['html'], string_types)
        self.assertEqual(attributes_by_name['html'], '<p>I <strong>am</strong> a test</p>')
        self.assertIsInstance(attributes_by_name['image'], string_types)
        self.assertEqual(attributes_by_name['image'], '/media/images/products/2018/01/IMG_3777.JPG')
        self.assertIsInstance(attributes_by_name['integer'], int)
        self.assertEqual(attributes_by_name['integer'], 7)
        self.assertIsInstance(attributes_by_name['multioption'], list)
        self.assertEqual(attributes_by_name['multioption'], ['Small', 'Large'])
        self.assertIsInstance(attributes_by_name['option'], string_types)
        self.assertEqual(attributes_by_name['option'], 'Small')

    def test_product_price(self):
        "See if we get the price information"
        self.response = self.get(reverse('product-price', args=(1,)))
        self.response.assertStatusEqual(200)
        self.assertIn('excl_tax', self.response.body)

        self.response = self.get(reverse('product-price', args=(999999,)))
        self.response.assertStatusEqual(404)

    def test_product_availability(self):
        "See if we get the availability information"
        self.response = self.get(reverse('product-availability', args=(1,)))
        self.response.assertStatusEqual(200)
        self.assertIn('num_available', self.response.body)

        self.response = self.get(reverse('product-availability', args=(999999,)))
        self.response.assertStatusEqual(404)
