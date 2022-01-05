from django.utils.translation import ugettext_lazy as _

from oscar.apps.basket import signals
from oscar.core.loading import get_model, get_class

from rest_framework import status, generics, exceptions
from rest_framework.response import Response
from rest_framework.views import APIView

from oscarapi import permissions
from oscarapi.basket import operations
from oscarapi.utils.loading import get_api_classes, get_api_class
from oscarapi.views.utils import BasketPermissionMixin

__all__ = (
    "BasketView",
    "LineList",
    "AddProductView",
    "BasketLineDetail",
    "AddVoucherView",
    "ShippingMethodView",
)

Basket = get_model("basket", "Basket")
Line = get_model("basket", "Line")
Repository = get_class("shipping.repository", "Repository")
ShippingAddress = get_model("order", "ShippingAddress")
(  # pylint: disable=unbalanced-tuple-unpacking
    BasketSerializer,
    VoucherAddSerializer,
    VoucherSerializer,
    BasketLineSerializer,
) = get_api_classes(
    "serializers.basket",
    [
        "BasketSerializer",
        "VoucherAddSerializer",
        "VoucherSerializer",
        "BasketLineSerializer",
    ],
)
AddProductSerializer = get_api_class("serializers.product", "AddProductSerializer")
(
    ShippingAddressSerializer,
    ShippingMethodSerializer,
) = get_api_classes(  # pylint: disable=unbalanced-tuple-unpacking
    "serializers.checkout", ["ShippingAddressSerializer", "ShippingMethodSerializer"]
)


class BasketView(APIView):
    """
    Api for retrieving a user's basket.

    GET:
    Retrieve your basket.
    """

    serializer_class = BasketSerializer

    def get(self, request, *args, **kwargs):  # pylint: disable=redefined-builtin
        basket = operations.get_basket(request)
        ser = self.serializer_class(basket, context={"request": request})
        return Response(ser.data)


class AddProductView(APIView):
    """
    Add a certain quantity of a product to the basket.

    POST(url, quantity)
    {
        "url": "http://testserver.org/oscarapi/products/209/",
        "quantity": 6
    }

    If you've got some options to configure for the product to add to the
    basket, you should pass the optional ``options`` property:
    {
        "url": "http://testserver.org/oscarapi/products/209/",
        "quantity": 6,
        "options": [{
            "option": "http://testserver.org/oscarapi/options/1/",
            "value": "some value"
        }]
    }
    """

    add_product_serializer_class = AddProductSerializer
    serializer_class = BasketSerializer

    def validate(
        self, basket, product, quantity, options
    ):  # pylint: disable=unused-argument
        availability = basket.strategy.fetch_for_product(product).availability

        # check if product is available at all
        if not availability.is_available_to_buy:
            return False, availability.message

        current_qty = basket.product_quantity(product)
        desired_qty = current_qty + quantity

        # check if we can buy this quantity
        allowed, message = availability.is_purchase_permitted(desired_qty)
        if not allowed:
            return False, message

        # check if there is a limit on amount
        allowed, message = basket.is_quantity_allowed(desired_qty)
        if not allowed:
            return False, message
        return True, None

    def post(self, request, *args, **kwargs):  # pylint: disable=redefined-builtin
        p_ser = self.add_product_serializer_class(
            data=request.data, context={"request": request}
        )
        if p_ser.is_valid():
            basket = operations.get_basket(request)
            product = p_ser.validated_data["url"]
            quantity = p_ser.validated_data["quantity"]
            options = p_ser.validated_data.get("options", [])

            basket_valid, message = self.validate(basket, product, quantity, options)
            if not basket_valid:
                return Response(
                    {"reason": message}, status=status.HTTP_406_NOT_ACCEPTABLE
                )

            basket.add_product(product, quantity=quantity, options=options)

            signals.basket_addition.send(
                sender=self, product=product, user=request.user, request=request
            )

            operations.apply_offers(request, basket)
            ser = self.serializer_class(basket, context={"request": request})
            return Response(ser.data)

        return Response({"reason": p_ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)


class AddVoucherView(APIView):
    """
    Add a voucher to the basket.

    POST(vouchercode)
    {
        "vouchercode": "kjadjhgadjgh7667"
    }

    Will return 200 and the voucher as json if successful.
    If unsuccessful, will return 406 with the error.
    """

    add_voucher_serializer_class = VoucherAddSerializer
    serializer_class = VoucherSerializer

    def post(self, request, *args, **kwargs):  # pylint: disable=redefined-builtin
        v_ser = self.add_voucher_serializer_class(
            data=request.data, context={"request": request}
        )
        if v_ser.is_valid():
            basket = operations.get_basket(request)

            voucher = v_ser.instance
            basket.vouchers.add(voucher)

            signals.voucher_addition.send(sender=None, basket=basket, voucher=voucher)

            # Recalculate discounts to see if the voucher gives any
            operations.apply_offers(request, basket)
            discounts_after = basket.offer_applications

            # Look for discounts from this new voucher
            for discount in discounts_after:
                if discount["voucher"] and discount["voucher"] == voucher:
                    break
            else:
                basket.vouchers.remove(voucher)
                return Response(
                    {
                        "reason": _(
                            "Your basket does not qualify for a voucher discount"
                        )
                    },  # noqa
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )

            ser = self.serializer_class(voucher, context={"request": request})
            return Response(ser.data)

        return Response(v_ser.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


class ShippingMethodView(APIView):
    """
    GET:
    Retrieve shipping methods available to the user, basket, request combination

    POST(shipping_address):
    {
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

    Post a shipping_address if your shipping methods are dependent on the
    address.
    """

    serializer_class = ShippingAddressSerializer
    shipping_method_serializer_class = ShippingMethodSerializer

    def _get(self, request, shipping_address=None):  # pylint: disable=redefined-builtin
        basket = operations.get_basket(request)
        shiping_methods = Repository().get_shipping_methods(
            basket=basket,
            user=request.user,
            shipping_addr=shipping_address,
            request=request,
        )
        ser = self.shipping_method_serializer_class(
            shiping_methods, many=True, context={"basket": basket}
        )
        return Response(ser.data)

    def get(self, request, *args, **kwargs):  # pylint: disable=redefined-builtin
        """
        Get the available shipping methods and their cost for this order.

        GET:
        A list of shipping method details and the prices.
        """
        return self._get(request)

    def post(self, request, *args, **kwargs):  # pylint: disable=redefined-builtin
        s_ser = self.serializer_class(data=request.data, context={"request": request})
        if s_ser.is_valid():
            shipping_address = ShippingAddress(**s_ser.validated_data)
            return self._get(request, shipping_address=shipping_address)

        return Response(s_ser.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


class LineList(BasketPermissionMixin, generics.ListCreateAPIView):
    """
    Api for adding lines to a basket.

    Permission will be checked,
    Regular users may only access their own basket,
    staff users may access any basket.

    GET:
    A list of basket lines.

    POST(basket, line_reference, product, stockrecord,
         quantity, price_currency, price_excl_tax, price_incl_tax):
    Add a line to the basket, example::

        {
            "basket": "http://127.0.0.1:8000/oscarapi/baskets/100/",
            "line_reference": "234_345",
            "product": "http://127.0.0.1:8000/oscarapi/products/209/",
            "stockrecord":
                "http://127.0.0.1:8000/ooscarapi/products/209/stockercords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0"
        }
    """

    permission_classes = (permissions.RequestAllowsAccessTo,)
    serializer_class = BasketLineSerializer
    queryset = Line.objects.all()

    def get_queryset(self):
        basket_pk = self.kwargs.get("pk")
        basket = self.check_basket_permission(self.request, basket_pk=basket_pk)
        prepped_basket = operations.assign_basket_strategy(basket, self.request)
        return prepped_basket.all_lines()

    def post(
        self, request, pk, format=None, *args, **kwargs
    ):  # pylint: disable=redefined-builtin,arguments-differ
        data_basket = self.get_data_basket(request.data, format)
        self.check_basket_permission(request, basket=data_basket)

        url_basket = self.check_basket_permission(request, basket_pk=pk)

        if url_basket != data_basket:
            raise exceptions.NotAcceptable(
                _("Target basket inconsistent %s != %s")
                % (url_basket.pk, data_basket.pk)
            )
        return super(LineList, self).post(request, format=format)


class BasketLineDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Only the field `quantity` can be changed in this view.
    All other fields are readonly.
    """

    queryset = Line.objects.all()
    serializer_class = BasketLineSerializer
    permission_classes = (permissions.RequestAllowsAccessTo,)

    def get_queryset(self):
        basket_pk = self.kwargs.get("basket_pk")
        basket = generics.get_object_or_404(operations.editable_baskets(), pk=basket_pk)
        prepped_basket = operations.prepare_basket(basket, self.request)
        if operations.request_allows_access_to_basket(self.request, prepped_basket):
            return prepped_basket.all_lines()
        else:
            return self.queryset.none()
