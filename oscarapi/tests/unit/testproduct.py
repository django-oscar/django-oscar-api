import mock
import  decimal

from six import string_types

from django.urls import reverse
from django.test import TestCase

from oscarapi.tests.utils import APITest
from oscarapi.serializers.product import ProductLinkSerializer, ProductAttributeValueSerializer
from oscarapi.serializers.basket import StockRecordSerializer


class ProductListDetailSerializer(ProductLinkSerializer):
    "subclass of ProductLinkSerializer to demonstrate showing details in listview"
    class Meta(ProductLinkSerializer.Meta):
        fields = (
            'url', 'id', 'title', 'structure', 'description', 'date_created',
            'date_updated', 'recommended_products', 'attributes',
            'categories', 'product_class', 'stockrecords', 'images',
            'price', 'availability', 'options', 'children'
        )


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

    def test_product_list_filter(self):
        standalone_products_url = "%s?structure=standalone" % reverse('product-list')
        self.response = self.get(standalone_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 2)

        parent_products_url = "%s?structure=parent" % reverse('product-list')
        self.response = self.get(parent_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        child_products_url = "%s?structure=child" % reverse('product-list')
        self.response = self.get(child_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        koe_products_url = "%s?structure=koe" % reverse('product-list')
        self.response = self.get(koe_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 0)

    @mock.patch('oscarapi.views.product.ProductList.get_serializer_class')
    def test_productlist_detail(self, get_serializer_class):
        "The product list should be able to render the same information as the detail page"
        # setup mocks
        get_serializer_class.return_value = ProductListDetailSerializer

        # define fields to check
        product_detail_fields = (
            'url', 'id', 'title', 'structure', 'description', 'date_created',
            'date_updated', 'recommended_products', 'attributes',
            'categories', 'product_class', 'stockrecords', 'images',
            'price', 'availability', 'options', 'children'
        )

        # fetch data
        parent_products_url = "%s?structure=parent" % reverse('product-list')
        self.response = self.get(parent_products_url)

        # make assertions
        get_serializer_class.assert_called_once_with()
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        # load product data
        products = self.response.json()
        product_with_children = products[0]

        self.assertEqual(product_with_children['structure'], 'parent',
            "since we filtered on structure=parent the list should contain items with structure=parent"
        )
        # verify all the fields are rendered in the list view
        for field in product_detail_fields:
            self.assertIn(field, product_with_children)

        children = product_with_children['children']
        self.assertEqual(len(children), 1, "There should be 1 child")
        child = children[0]
        
        self.assertEqual(child['structure'], 'child',
            "the child should have structure=child"
        )
        self.assertNotEqual(product_with_children['id'], child['id'])
        self.assertNotEqual(product_with_children['structure'], child['structure'])
        self.assertNotIn('description', child, "child should not have a description by default")
        self.assertNotIn('images', child, "child should not have images by default")

    def test_product_detail(self):
        "Check product details"
        self.response = self.get(reverse('product-detail', args=(1,)))
        self.response.assertStatusEqual(200)
        default_fields = (
            'url', 'id', 'title', 'structure', 'description', 'date_created',
            'date_updated', 'recommended_products', 'attributes',
            'categories', 'product_class', 'stockrecords', 'images',
            'price', 'availability', 'options', 'children'
        )
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


class ProductSerializerTest(TestCase):
    fixtures = [
        'product', 'productcategory', 'productattribute', 'productclass',
        'productattributevalue', 'category', 'attributeoptiongroup',
        'attributeoption', 'stockrecord', 'partner'
    ]

    def test_stockrecord_save(self):
        ser = StockRecordSerializer(data={
            "product": 1,
            "partner": 1,
            "partner_sku": "henk",
            "price_currency": "EUR",
            "price_excl_tax": 20,
            "price_retail": 36,
            "cost_price": 11,
            "num_in_stock": 34,
            "low_stock_threshold": 4
        })
        self.assertTrue(ser.is_valid(), "There where errors %s" % ser.errors)

        obj = ser.save()
        self.assertEqual(obj.product.get_title(), "Oscar T-shirt")
        self.assertEqual(obj.partner.name, "Book partner")
        self.assertEqual(obj.price_currency, "EUR")
        self.assertEqual(obj.price_excl_tax, decimal.Decimal("20.00"))
        self.assertEqual(obj.price_retail, decimal.Decimal("36.00"))
        self.assertEqual(obj.cost_price, decimal.Decimal("11.00"))
        self.assertEqual(obj.num_in_stock, 34)
        self.assertEqual(obj.low_stock_threshold, 4)
        self.assertEqual(obj.num_allocated, None)


    def test_productattributevalueserializer_error(self):
        ser = ProductAttributeValueSerializer(data={
            "name": "zult",
            "code": "zult",
            "value": "hoolahoop",
            "product": 1
        })
        
        self.assertFalse(ser.is_valid(),
            "There should be an error because there is no attribute named zult") 
        self.assertEqual(ser.errors["non_field_errors"], [
            "No attribute zult with code=zult on Oscar T-shirt, please define "
            "it in the product_class first."
        ])

    def test_productattributevalueserializer(self):
        ser = ProductAttributeValueSerializer(data={
            "name": "Size",
            "code": "size",
            "value": "Small",
            "product": 1
        })
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
