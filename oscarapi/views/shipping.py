# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import status, views, response

from oscarapi.serializers import ShippingSerializer
from oscarapi.views.utils import BasketPermissionMixin

class ShippingView(BasketPermissionMixin, views.APIView):
    """
    Prepare a shipping method code and shipping charge for checkout.

    POST(basket, shipping_method_code, shipping_address):
    {
        "basket": "http://testserver/oscarapi/baskets/1/",
        "shipping_method_code": "free",
        "shipping_address": {
            "country": "http://127.0.0.1:8000/oscarapi/countries/NL/",
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
    returns the shipping method code and shipping charge.
    """
    def post(self, request, format=None):
        # TODO: Make it possible to create orders with options.
        # at the moment, no options are passed to this method, which means they
        # are also not created.

        data_basket = self.get_data_basket(request.DATA, format)
        basket = self.check_basket_permission(request,
                                              basket_pk=data_basket.pk)

        # by now an error should have been raised if someone was messing
        # around with the basket, so asume invariant
        assert(data_basket == basket)

        ship_ser = ShippingSerializer(data=request.DATA,
                                   context={'request': request})

        if ship_ser.is_valid():
            return response.Response(ship_ser.object)

        return response.Response(ship_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)