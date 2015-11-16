import json
from django.conf import settings
from django.core.urlresolvers import reverse

from oscar.core.loading import get_model

from oscarapi.tests.utils import APITest


Basket = get_model('basket', 'Basket')


class OfferTest(APITest):
    fixtures = [
        'product', 'productcategory', 'productattribute', 'productclass',
        'productattributevalue', 'category', 'attributeoptiongroup', 'attributeoption',
        'stockrecord', 'partner', 'offer'
    ]

    def setUp(self):
        # make sure we have this disabled for most of the tests
        settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = None
        super(OfferTest, self).setUp()

    def test_basket_discount(self):
        "A discount should be properly applied to the basket total"
        self.response = self.post('api-basket-add-product', url="http://testserver/api/products/1/", quantity=5)
        self.response.assertStatusEqual(200)

        self.response.assertValueEqual('total_excl_tax', "42.00")
        self.response.assertValueEqual('total_incl_tax', "42.00")
        self.response.assertValueEqual('total_excl_tax_excl_discounts', "50.00")
        self.response.assertValueEqual('total_incl_tax_excl_discounts', "50.00")

    def test_basket_line_discount(self):
        "A discount should be properly applied to the basket line"
        self.test_basket_discount()
        self.response = self.get(self.response['lines'])
        self.assertEqual(len(self.response.body), 1)
        line0 = self.response.body[0]
        self.assertEqual(line0['product'], "http://testserver/api/products/1/")
        self.assertEqual(line0['quantity'], 5)
        self.assertEqual(line0['price_excl_tax'], "42.00")
        self.assertEqual(line0['price_incl_tax'], "42.00")
        self.assertEqual(line0['price_excl_tax_excl_discounts'], "50.00")
        self.assertEqual(line0['price_incl_tax_excl_discounts'], "50.00")
