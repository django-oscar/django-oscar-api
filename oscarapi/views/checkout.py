from rest_framework import status, views, response

from oscarapi.serializers import OrderSerializer, CheckoutSerializer
from oscarapi.views.utils import BasketPermissionMixin


class CheckoutView(BasketPermissionMixin, views.APIView):
    """
    Prepare an order for checkout.

    POST(basket, total, shipping_address,
         [shipping_method_code, shipping_charge, billing_address]):
    {
        "basket": "http://testserver/oscarapi/baskets/1/",
        "total": {
            "currency": "EUR",
            "excl_tax": "100.0",
            "tax": "21.0"
        },
        "shipping_charge": {
            "currency": "EUR",
            "excl_tax": "10.0",
            "tax": "0.6"
        },
        "shipping_method_code": "no-shipping-required",
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
    returns the order object.
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

        c_ser = CheckoutSerializer(data=request.DATA,
                                   context={'request': request})
        if c_ser.is_valid():
            order = c_ser.object
            basket.freeze()
            o_ser = OrderSerializer(order, context={'request': request})
            return response.Response(o_ser.data)

        return response.Response(c_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)
