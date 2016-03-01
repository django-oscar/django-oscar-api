from rest_framework import status, views, response, generics

from oscar.core.loading import get_model
from oscarapi.serializers import (
    OrderSerializer,
    CheckoutSerializer,
    OrderLineSerializer,
    OrderLineAttributeSerializer
)
from oscarapi.permissions import IsOwner
from oscarapi.views.utils import BasketPermissionMixin
from oscarapi.signals import oscarapi_post_checkout

Order = get_model('order', 'Order')
OrderLine = get_model('order', 'Line')
OrderLineAttribute = get_model('order', 'LineAttribute')

__all__ = (
    'CheckoutView',
    'OrderList', 'OrderDetail',
    'OrderLineList', 'OrderLineDetail',
    'OrderLineAttributeDetail'
)


class OrderList(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        qs = Order.objects.all()
        return qs.filter(user=self.request.user)


class OrderDetail(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsOwner,)


class OrderLineList(generics.ListAPIView):
    queryset = OrderLine.objects.all()
    serializer_class = OrderLineSerializer

    def get(self, request, pk=None, format=None):
        if pk is not None:
            self.queryset = self.queryset.filter(
                order__id=pk, order__user=request.user)
        elif not request.user.is_staff:
            self.permission_denied(request)

        return super(OrderLineList, self).get(request, format)


class OrderLineDetail(generics.RetrieveAPIView):
    queryset = OrderLine.objects.all()
    serializer_class = OrderLineSerializer

    def get(self, request, pk=None, format=None):
        if not request.user.is_staff:
            self.queryset = self.queryset.filter(
                order__id=pk, order__user=request.user)

        return super(OrderLineDetail, self).get(request, format)


class OrderLineAttributeDetail(generics.RetrieveAPIView):
    queryset = OrderLineAttribute.objects.all()
    serializer_class = OrderLineAttributeSerializer


class CheckoutView(BasketPermissionMixin, views.APIView):
    """
    Prepare an order for checkout.

    POST(basket, shipping_address,
         [total, shipping_method_code, shipping_charge, billing_address]):
    {
        "basket": "http://testserver/oscarapi/baskets/1/",
        "guest_email": "foo@example.com",
        "total": "100.0",
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
    order_serializer_class = OrderSerializer
    serializer_class = CheckoutSerializer

    def post(self, request, format=None):
        # TODO: Make it possible to create orders with options.
        # at the moment, no options are passed to this method, which means they
        # are also not created.

        data_basket = self.get_data_basket(request.data, format)
        basket = self.check_basket_permission(request,
                                              basket_pk=data_basket.pk)

        # by now an error should have been raised if someone was messing
        # around with the basket, so asume invariant
        assert(data_basket == basket)

        c_ser = self.serializer_class(
            data=request.data, context={'request': request})
        if c_ser.is_valid():
            order = c_ser.save()
            basket.freeze()
            o_ser = self.order_serializer_class(
                order, context={'request': request})
            oscarapi_post_checkout.send(
                sender=self, order=order, user=request.user,
                request=request, response=response)
            return response.Response(o_ser.data)

        return response.Response(c_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)
