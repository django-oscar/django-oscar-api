from commerceconnect.tests.utils import APITest
import json
"""
{
    "
}
"""
class CheckOutTest(APITest):
    fixtures = [
        'product', 'productcategory', 'productattribute', 'productclass',
        'productattributevalue', 'category', 'attributeoptiongroup', 'attributeoption',
        'stockrecord', 'partner', 'orderanditemcharges', 'country'
    ]
    
    def test_checkout(self):
        "Let's see if it does anything"
        self.login(username='nobody', password='nobody')
        response = self.get('api-basket')
        self.assertTrue(response.status_code, 200)
        basket_url = json.loads(response.content).get('url')
        
        request = {
            'basket': basket_url,
            'total': {
                'currency': 'EUR',
                'excl_tax':'100.0',
                'tax':'21.0'
            },
            'shipping_method': "http://127.0.0.1:8000/commerceconnect/shippingmethods/1/",
            'shipping_charge': {
                'currency': 'EUR',
                'excl_tax':'10.0',
                'tax':'0.6'
            },
            "shipping_address": {
                "country": "http://127.0.0.1:8000/commerceconnect/countries/NL/",
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
        response = self.post('api-checkout', **request)
        self.assertEqual(response.status_code, 406)
        response = self.post('api-basket-add-product', url="http://testserver/commerceconnect/products/1/", quantity=5)
        self.assertEqual(response.status_code, 200)
        response = self.post('api-checkout', **request)

        self.assertEqual(response.status_code, 200)

