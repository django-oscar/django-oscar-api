# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import unittest

from oscar.core.loading import get_model
from oscarapi.tests.utils import APITest


Basket = get_model('basket', 'Basket')


class ShippingTest(APITest):
    fixtures = [
        'product', 'productcategory', 'productattribute', 'productclass',
        'productattributevalue', 'category', 'attributeoptiongroup', 'attributeoption',
        'stockrecord', 'partner', 'orderanditemcharges', 'country'
    ]

    def test_checkout(self):
        "Test if an order can be placed as an authenticated user with session based auth."
        self.login(username='nobody', password='nobody')
        response = self.get('api-basket')
        self.assertTrue(response.status_code, 200)
        basket = json.loads(response.content)
        basket_url = basket.get('url')

        request = {
            'basket': basket_url,
            "shipping_address": {
                "country": "http://127.0.0.1:8000/api/countries/NL/",
                "first_name": "Henk",
                "last_name": "Van den Heuvel",
                "line1": "Roemerlaan 44",
                "line2": "",
                "line3": "",
                "line4": "Kroekingen",
                "notes": "Niet STUK MAKEN OK!!!!",
                "phone_number": "+31 26 370 4887",
                "postcode": "7777KK",
                "state": "Gerendrecht",
                "title": "Mr"
            }
        }
        response = self.post('api-shipping', **request)
        self.assertEqual(response.status_code, 406)
        response = self.post('api-basket-add-product', url="http://testserver/api/products/1/", quantity=5)
        self.assertEqual(response.status_code, 200)
        response = self.post('api-shipping', **request)

        self.assertEqual(response.status_code, 200)
