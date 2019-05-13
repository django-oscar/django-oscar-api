import mock
import  decimal
import datetime
from six import string_types

from django.urls import reverse
from django.test import TestCase
from django.utils.timezone import make_aware

from oscar.core.loading import get_model
from oscarapi.tests.utils import APITest
from oscarapi.serializers.fields import CategoryField
from oscarapi.serializers.product import ProductLinkSerializer, ProductAttributeValueSerializer
from oscarapi.serializers.basket import StockRecordSerializer
from oscarapi.serializers.admin.product import AdminProductSerializer

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")


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


class _ProductSerializerTest(TestCase):
    fixtures = [
        'product', 'productcategory', 'productattribute', 'productclass',
        'productattributevalue', 'category', 'attributeoptiongroup',
        'attributeoption', 'stockrecord', 'partner'
    ]

    def assertErrorStartsWith(self, ser, name, errorstring):
        self.assertTrue(ser.errors[name][0].startswith(errorstring),
            "Error does not start with %s" % errorstring)


class StockRecordSerializerTest(_ProductSerializerTest):
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


class ProductAttributeValueSerializerTest(_ProductSerializerTest):
    def test_productattributevalueserializer_error(self):
        ser = ProductAttributeValueSerializer(data={
            "name": "zult",
            "code": "zult",
            "value": "hoolahoop",
            "product": 1
        })
        
        self.assertFalse(ser.is_valid(),
            "There should be an error because there is no attribute named zult") 
        self.assertEqual(ser.errors["value"], [
            "No attribute exist named zult with code=zult, please define it in "
            "the product_class first."
        ])

    def test_productattributevalueserializer_option(self):
        p = Product.objects.get(pk=1)
        self.assertEqual(str(p.attr.size), "Small")
        ser = ProductAttributeValueSerializer(data={
            "name": "Size",
            "code": "size",
            "value": "Large",
            "product": 1
        })
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(str(obj.value), "Large")

        p.attr.initiate_attributes()
        self.assertEqual(str(p.attr.size), "Large")

    def test_productattributevalueserializer_option_error(self):
        p = Product.objects.get(pk=1)
        self.assertEqual(str(p.attr.size), "Small")
        ser = ProductAttributeValueSerializer(data={
            "name": "Size",
            "code": "size",
            "value": "LUL",
            "product": 1
        })
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(ser.errors, {"value": ["Option LUL does not exist."]})

        ser = ProductAttributeValueSerializer(data={
            "name": "Size",
            "code": "size",
            "value": None,
            "product": 1
        })
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(ser.errors, {"value": ["This field is required."]})

    def test_productattributevalueserializer_text(self):
        p = Product.objects.get(pk=3)
        self.assertEqual(p.attr.text, "I am some kind of text")
        ser = ProductAttributeValueSerializer(data={
            "name": "Text",
            "code": "text",
            "value": "Donec placerat. Nullam nibh dolor.",
            "product": 3
        })
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, "Donec placerat. Nullam nibh dolor.")

        p.attr.initiate_attributes()
        self.assertEqual(p.attr.text, "Donec placerat. Nullam nibh dolor.")

    def test_productattributevalueserializer_text_error(self):
        p = Product.objects.get(pk=3)
        self.assertEqual(p.attr.text, "I am some kind of text")
        ser = ProductAttributeValueSerializer(data={
            "name": "Text",
            "code": "text",
            "value": 4,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should fail")

        ser = ProductAttributeValueSerializer(data={
            "name": "Text",
            "code": "text",
            "value": None,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should fail")
        self.assertDictEqual(ser.errors, {"value": ["This field is required."]})

    def test_productattributevalueserializer_integer(self):
        p = Product.objects.get(pk=3)
        self.assertEqual(p.attr.integer, 7)
        
        ser = ProductAttributeValueSerializer(data={
            "name": "Integer",
            "code": "integer",
            "value": 4,
            "product": 3
        })
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, 4)

        p.attr.initiate_attributes()
        self.assertEqual(p.attr.integer, 4)

        ser = ProductAttributeValueSerializer(data={
            "name": "Integer",
            "code": "integer",
            "value": "34",
            "product": 3
        })
        self.assertTrue(ser.is_valid(), "Even if the type is wrong, it should still validate because its an integer")
        obj = ser.save()
        self.assertEqual(obj.value, 34)

    def test_productattributevalueserializer_integer_error(self):
        p = Product.objects.get(pk=3)
        self.assertEqual(p.attr.integer, 7)
        
        ser = ProductAttributeValueSerializer(data={
            "name": "Integer",
            "code": "integer",
            "value": "zult",
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(ser.errors, {"value": ["Must be an integer"]})

        ser = ProductAttributeValueSerializer(data={
            "name": "Integer",
            "code": "integer",
            "value": None,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(ser.errors, {"value": ["This field is required."]})

    def test_productattributevalueserializer_boolean(self):
        p = Product.objects.get(pk=3)
        self.assertEqual(p.attr.boolean, True)
        ser = ProductAttributeValueSerializer(data={
            "name": "Boolean",
            "code": "boolean",
            "value": False,
            "product": 3
        })
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, False)

        p.attr.initiate_attributes()
        self.assertEqual(p.attr.boolean, False)

    def test_productattributevalueserializer_boolean_error(self):
        p = Product.objects.get(pk=3)
        self.assertEqual(p.attr.boolean, True)
        ser = ProductAttributeValueSerializer(data={
            "name": "Boolean",
            "code": "boolean",
            "value": object,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate, an object is not a boolean")
        self.assertDictEqual(ser.errors, {"value": ["Must be a boolean"]})

        ser = ProductAttributeValueSerializer(data={
            "name": "Boolean",
            "code": "boolean",
            "value": None,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate, empty is not allowed")
        self.assertDictEqual(ser.errors, {"value": ["This field is required."]})

        ser = ProductAttributeValueSerializer(data={
            "name": "Boolean",
            "code": "boolean",
            "value": 0,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate, an object is not a boolean")
        self.assertDictEqual(ser.errors, {"value": ["Must be a boolean"]})

        ser = ProductAttributeValueSerializer(data={
            "name": "Boolean",
            "code": "boolean",
            "value": "",
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate, an object is not a boolean")
        self.assertDictEqual(ser.errors, {"value": ["Must be a boolean"]})

    def test_productattributevalueserializer_float(self):
        p = Product.objects.get(pk=3)
        self.assertEqual(p.attr.float, 3.2)
        ser = ProductAttributeValueSerializer(data={
            "name": "Float",
            "code": "float",
            "value": 7.78,
            "product": 3
        })
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, 7.78)

        p.attr.initiate_attributes()
        self.assertEqual(p.attr.float, 7.78)

        ser = ProductAttributeValueSerializer(data={
            "name": "Float",
            "code": "float",
            "value": 7,
            "product": 3
        })
        self.assertTrue(ser.is_valid(), "If the value is an int it should still work")
        obj = ser.save()
        self.assertEqual(obj.value, 7)

        p.attr.initiate_attributes()
        self.assertEqual(p.attr.float, 7)

        ser = ProductAttributeValueSerializer(data={
            "name": "Float",
            "code": "float",
            "value": "7.78",
            "product": 3
        })
        self.assertTrue(ser.is_valid(), "If a string is a float it should still work")
        obj = ser.save()
        self.assertEqual(obj.value, 7.78)

        p.attr.initiate_attributes()
        self.assertEqual(p.attr.float, 7.78)

    def test_productattributevalueserializer_float_error(self):
        p = Product.objects.get(pk=3)
        self.assertEqual(p.attr.float, 3.2)
        ser = ProductAttributeValueSerializer(data={
            "name": "Float",
            "code": "float",
            "value": {},
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not be valid, a dict is not a float")
        self.assertErrorStartsWith(ser, "value", "Wrong type, float() argument must be a string or a number")

        ser = ProductAttributeValueSerializer(data={
            "name": "Float",
            "code": "float",
            "value": object,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not be valid, a dict is not a float")
        self.assertErrorStartsWith(ser, "value", "Wrong type, float() argument must be a string or a number")

        ser = ProductAttributeValueSerializer(data={
            "name": "Float",
            "code": "float",
            "value": "kak",
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not be valid, a dict is not a float")
        self.assertDictEqual(ser.errors, {"value": ["Must be a float"]})


    def test_productattributevalueserializer_html(self):
        p = Product.objects.get(pk=3)
        self.assertEqual(p.attr.html, "<p>I <strong>am</strong> a test</p>")
        ser = ProductAttributeValueSerializer(data={
            "name": "Html",
            "code": "html",
            "value": "<p>koe</p>",
            "product": 3
        })
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, "<p>koe</p>")

        p.attr.initiate_attributes()
        self.assertEqual(p.attr.html, "<p>koe</p>")

    def test_productattributevalueserializer_html_error(self):
        p = Product.objects.get(pk=3)
        self.assertEqual(p.attr.text, "I am some kind of text")
        ser = ProductAttributeValueSerializer(data={
            "name": "Html",
            "code": "html",
            "value": 4,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should fail")

        ser = ProductAttributeValueSerializer(data={
            "name": "Html",
            "code": "html",
            "value": None,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should fail")
        self.assertDictEqual(ser.errors, {"value": ["This field is required."]})

        ser = ProductAttributeValueSerializer(data={
            "name": "Html",
            "code": "html",
            "value": object,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should fail")

    def test_productattributevalueserializer_date(self):
        p = Product.objects.get(pk=3)
        start_date = datetime.date(2018, 1, 2)
        self.assertEqual(p.attr.date, start_date)
        ser = ProductAttributeValueSerializer(data={
            "name": "Date",
            "code": "date",
            "value": "2030-03-03",
            "product": 3
        })
        new_date = datetime.date(2030, 3, 3)
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, new_date)

        p.attr.initiate_attributes()
        self.assertEqual(p.attr.date, new_date)

        ser = ProductAttributeValueSerializer(data={
            "name": "Date",
            "code": "date",
            "value": datetime.date(2016, 4, 12),
            "product": 3
        })
        new_date = datetime.date(2016, 4, 12)
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, new_date)

        p.attr.initiate_attributes()
        self.assertEqual(p.attr.date, new_date)

    def test_productattributevalueserializer_date_error(self):
        p = Product.objects.get(pk=3)
        ser = ProductAttributeValueSerializer(data={
            "name": "Date",
            "code": "date",
            "value": "2030",
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertErrorStartsWith(ser, "value", "Date has wrong format. Use one of these formats instead:")

        ser = ProductAttributeValueSerializer(data={
            "name": "Date",
            "code": "date",
            "value": "zult",
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertErrorStartsWith(ser, "value", "Date has wrong format. Use one of these formats instead:")

        ser = ProductAttributeValueSerializer(data={
            "name": "Date",
            "code": "date",
            "value": None,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(ser.errors, {"value": ["This field is required."]})

        ser = ProductAttributeValueSerializer(data={
            "name": "Date",
            "code": "date",
            "value": {},
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertErrorStartsWith(ser, "value", "Date has wrong format. Use one of these formats instead:")

    def test_productattributevalueserializer_datetime(self):
        p = Product.objects.get(pk=3)
        start_date = make_aware(datetime.datetime(2018, 1, 2, 10, 45))
        self.assertEqual(p.attr.datetime, start_date)
        ser = ProductAttributeValueSerializer(data={
            "name": "Datetime",
            "code": "datetime",
            "value": "2030-03-03T01:12",
            "product": 3
        })
        new_date = make_aware(datetime.datetime(2030, 3, 3, 1, 12))
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, new_date)

        p.attr.initiate_attributes()
        self.assertEqual(p.attr.datetime, new_date)

    def test_productattributevalueserializer_datetime_error(self):
        p = Product.objects.get(pk=3)
        ser = ProductAttributeValueSerializer(data={
            "name": "Datetime",
            "code": "datetime",
            "value": "2030-03-03LOL01:12",
            "product": 3
        })
        self.assertFalse(ser.is_valid(), str(ser.errors))
        self.assertErrorStartsWith(ser, "value", "Datetime has wrong format. Use one of these formats instead:")

        ser = ProductAttributeValueSerializer(data={
            "name": "Datetime",
            "code": "datetime",
            "value": None,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), str(ser.errors))
        self.assertDictEqual(ser.errors, {"value": ["This field is required."]})

        ser = ProductAttributeValueSerializer(data={
            "name": "Datetime",
            "code": "datetime",
            "value": list,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), str(ser.errors))
        self.assertErrorStartsWith(ser, "value", "Datetime has wrong format. Use one of these formats instead:")

    def test_productattributevalueserializer_multioption(self):
        p = Product.objects.get(pk=3)
        self.assertEqual([str(o) for o in p.attr.multioption], ["Small", "Large"])
        
        ser = ProductAttributeValueSerializer(data={
            "name": "Multioption",
            "code": "multioption",
            "value": ["Large"],
            "product": 3
        })
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual([str(o) for o in obj.value], ["Large"])

        p.attr.initiate_attributes()
        self.assertEqual([str(o) for o in p.attr.multioption], ["Large"])

    def test_productattributevalueserializer_multioption_error(self):
        p = Product.objects.get(pk=3)
        ser = ProductAttributeValueSerializer(data={
            "name": "Multioption",
            "code": "multioption",
            "value": [],
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(ser.errors, {"value": ["This field is required."]})

        ser = ProductAttributeValueSerializer(data={
            "name": "Multioption",
            "code": "multioption",
            "value": None,
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(ser.errors, {"value": ["This field is required."]})

        ser = ProductAttributeValueSerializer(data={
            "name": "Multioption",
            "code": "multioption",
            "value": ["Large", "kip", "geit"],
            "product": 3
        })
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(ser.errors, {"value": ["Option geit,kip does not exist."]})


class CategoryFieldTest(_ProductSerializerTest):
    def test_write(self):
        self.assertEqual(Category.objects.count(), 1)
        ser = CategoryField(many=True, required=False)
        data=[
            "Henk > is > een > keel",
            "En > klaas > is > er > ook > een"
        ]
        validated_data = ser.run_validation(data)
        self.assertEqual(len(validated_data), 2)
        first, second = validated_data
        self.assertEqual(first.full_slug, "henk/is/een/keel")
        self.assertEqual(second.full_slug, "en/klaas/is/er/ook/een")
        self.assertEqual(Category.objects.count(), 11)

    def test_read(self):
        self.test_write()
        ser = CategoryField(many=True, required=False)
        val = ser.to_representation(Category.objects.filter(pk__in=[7, 4]))
        self.assertListEqual(val, ["Henk > is > een", "En > klaas"])


class AdminProductSerializerTest(_ProductSerializerTest):
    def test_create_product(self):
        ser = AdminProductSerializer(data={
            "product_class": "testtype",
            "slug": "new-product",
        })
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 5)
        self.assertEqual(obj.product_class.slug, "testtype")
        self.assertEqual(obj.slug, "new-product")

    def test_modify_product(self):
        product = Product.objects.get(pk=3)
        self.assertEqual(product.upc, "attrtypestest")
        self.assertEqual(product.description, "<p>It is a test for the attributes</p>")

        ser = AdminProductSerializer(data={
            "id": 3,
            "product_class": "testtype",
            "slug": "lots-of-attributes",
            "description": "Henk",
        }, instance=product)
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.upc, "attrtypestest")
        self.assertEqual(obj.description, "Henk")

    def test_modify_product_error(self):
        product = Product.objects.get(pk=3)
        self.assertEqual(product.upc, "attrtypestest")
        self.assertEqual(product.description, "<p>It is a test for the attributes</p>")

        ser = AdminProductSerializer(data={
            "id": 3,
            "product_class": "testtype",
            "slug": "lots-of-attributes",
            "description": "Henk",
            "attributes": [
                {
                    "name": "Text",
                    "value": "Blaat blaat",
                }
            ]
        }, instance=product)
        self.assertFalse(ser.is_valid(), "Should fail because of missing code")
        self.assertDictEqual(ser.errors, {"attributes": [{"code": "This field is required."}]})

    def test_switch_product_class(self):
        product = Product.objects.get(pk=3)
        self.assertEqual(product.attribute_values.count(), 11)
        self.assertEqual(product.attr.boolean, True)
        self.assertEqual(product.attr.date, datetime.date(2018, 1, 2))
        self.assertEqual(product.attr.datetime, make_aware(datetime.datetime(2018, 1, 2, 10, 45)))
        self.assertEqual(product.attr.float, 3.2)
        self.assertEqual(product.attr.html, "<p>I <strong>am</strong> a test</p>")
        self.assertEqual(product.attr.integer, 7)
        self.assertEqual([str(a) for a in product.attr.multioption], ['Small', 'Large'])
        self.assertEqual(str(product.attr.option), "Small")
        
        ser = AdminProductSerializer(data={
            "id": 3,
            "product_class": "t-shirt",
            "slug": "lots-of-attributes",
            "description": "Henk",
            "attributes": [
                {
                    "name": "Size",
                    "value": "Large",
                    "code": "size"
                }
            ]
        }, instance=product)
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()

        self.assertEqual(obj.product_class.slug, "t-shirt")

        # reset the annoying attr object, it stinks!!
        obj.attr.__dict__ = {}
        obj.attr.product = obj
        obj.attr.initiate_attributes()
        self.assertEqual(obj.attribute_values.count(), 1,
            "Only one attribute should be present now, because the new "
            "product class has none of the old atributes"
        )
        self.assertEqual(str(obj.attr.size), "Large")

        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.date, datetime.date(2018, 1, 2))
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.boolean, True)
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.datetime, make_aware(datetime.datetime(2018, 1, 2, 10, 45)))
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.float, 3.2)
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.html, "<p>I <strong>am</strong> a test</p>")
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.integer, 7)
        with self.assertRaises(AttributeError):
            self.assertNotEqual([str(a) for a in obj.attr.multioption], ['Small', 'Large'])
        with self.assertRaises(AttributeError):
            self.assertNotEqual(str(obj.attr.option), "Small")
