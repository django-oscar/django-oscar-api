from oscar.core.loading import get_model

from rest_framework import generics, response, status, views

from oscarapi.basket.operations import request_allows_access_to_basket
from oscarapi.permissions import IsOwner
from oscarapi.utils.loading import get_api_classes
from oscarapi.signals import oscarapi_post_checkout
from oscarapi.views.utils import parse_basket_from_hyperlink

Order = get_model("order", "Order")
OrderLine = get_model("order", "Line")
OrderLineAttribute = get_model("order", "LineAttribute")
UserAddress = get_model("address", "UserAddress")
(
    CheckoutSerializer,
    OrderLineAttributeSerializer,
    OrderLineSerializer,
    OrderSerializer,
    UserAddressSerializer,
) = get_api_classes(
    "serializers.checkout",
    [
        "CheckoutSerializer",
        "OrderLineAttributeSerializer",
        "OrderLineSerializer",
        "OrderSerializer",
        "UserAddressSerializer",
    ],
)

__all__ = (
    "CheckoutView",
    "OrderList",
    "OrderDetail",
    "OrderLineList",
    "OrderLineDetail",
    "OrderLineAttributeDetail",
    "UserAddressList",
    "UserAddressDetail",
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

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        user = self.request.user
        return super().get_queryset().filter(order_id=pk, order__user=user)


class OrderLineDetail(generics.RetrieveAPIView):
    queryset = OrderLine.objects.all()
    serializer_class = OrderLineSerializer

    def get_queryset(self):
        return super().get_queryset().filter(order__user=self.request.user)


class OrderLineAttributeDetail(generics.RetrieveAPIView):
    queryset = OrderLineAttribute.objects.all()
    serializer_class = OrderLineAttributeSerializer


class CheckoutView(views.APIView):
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
        "billing_address": {
            "country": country_url,
            "first_name": "Jos",
            "last_name": "Henken",
            "line1": "Boerderijstraat 19",
            "line2": "",
            "line3": "",
            "line4": "Zwammerdam",
            "notes": "",
            "phone_number": "+31 27 112 9800",
            "postcode": "6666LL",
            "state": "Gerendrecht",
            "title": "Mr"
         }
    }
    returns the order object.
    """

    order_serializer_class = OrderSerializer
    serializer_class = CheckoutSerializer

    def post(self, request, format=None, *args, **kwargs):
        # TODO: Make it possible to create orders with options.
        # at the moment, no options are passed to this method, which means they
        # are also not created.

        basket = parse_basket_from_hyperlink(request.data, format)

        if not request_allows_access_to_basket(request, basket):
            return response.Response(
                "Unauthorized", status=status.HTTP_401_UNAUTHORIZED
            )

        c_ser = self.serializer_class(data=request.data, context={"request": request})

        if c_ser.is_valid():
            order = c_ser.save()
            basket.freeze()
            o_ser = self.order_serializer_class(order, context={"request": request})

            resp = response.Response(o_ser.data)

            oscarapi_post_checkout.send(
                sender=self,
                order=order,
                user=request.user,
                request=request,
                response=resp,
            )
            return resp

        return response.Response(c_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)


class UserAddressList(generics.ListCreateAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)


class UserAddressDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)
