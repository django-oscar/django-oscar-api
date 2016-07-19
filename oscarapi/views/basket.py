from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from oscar.apps.basket import signals
from oscar.core.loading import get_model, get_class

from rest_framework import status, generics, exceptions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from oscarapi import serializers, permissions
from oscarapi.basket import operations
from oscarapi.views.mixin import PutIsPatchMixin
from oscarapi.views.utils import BasketPermissionMixin

__all__ = ('BasketView', 'LineList', 'LineDetail', 'AddProductView',
           'BasketLineDetail', 'AddVoucherView', 'shipping_methods')

Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')
Repository = get_class('shipping.repository', 'Repository')


class BasketView(APIView):
    """
    Api for retrieving a user's basket.

    GET:
    Retrieve your basket.
    """
    serializer_class = serializers.BasketSerializer

    def get(self, request, format=None):
        basket = operations.get_basket(request)
        ser = self.serializer_class(basket, context={'request': request})
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
    add_product_serializer_class = serializers.AddProductSerializer
    serializer_class = serializers.BasketSerializer

    def validate(self, basket, product, quantity, options):
        availability = basket.strategy.fetch_for_product(
            product).availability

        # check if product is available at all
        if not availability.is_available_to_buy:
            return False, availability.message

        # check if we can buy this quantity
        allowed, message = availability.is_purchase_permitted(quantity)
        if not allowed:
            return False, message

        # check if there is a limit on amount
        allowed, message = basket.is_quantity_allowed(quantity)
        if not allowed:
            return False, message
        return True, None

    def post(self, request, format=None):
        p_ser = self.add_product_serializer_class(
            data=request.data, context={'request': request})
        if p_ser.is_valid():
            basket = operations.get_basket(request)
            product = p_ser.validated_data['url']
            quantity = p_ser.validated_data['quantity']
            options = p_ser.validated_data.get('options', [])

            basket_valid, message = self.validate(
                basket, product, quantity, options)
            if not basket_valid:
                return Response(
                    {'reason': message},
                    status=status.HTTP_406_NOT_ACCEPTABLE)

            basket.add_product(product, quantity=quantity, options=options)
            operations.apply_offers(request, basket)
            ser = self.serializer_class(
                basket, context={'request': request})
            return Response(ser.data)

        return Response(
            {'reason': p_ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)


class AddVoucherView(APIView):
    """
    Add a voucher to the basket.

    POST(vouchercode)
    {
        "vouchercode": "kjadjhgadjgh7667"
    }

    Will return 200 and the voucher as json if succesful.
    If unsuccessful, will return 406 with the error.
    """
    add_voucher_serializer_class = serializers.VoucherAddSerializer
    serializer_class = serializers.VoucherSerializer

    def post(self, request, format=None):
        v_ser = self.add_voucher_serializer_class(
            data=request.data, context={'request': request})
        if v_ser.is_valid():
            basket = operations.get_basket(request)

            voucher = v_ser.instance
            basket.vouchers.add(voucher)

            signals.voucher_addition.send(
                sender=None, basket=basket, voucher=voucher)

            # Recalculate discounts to see if the voucher gives any
            operations.apply_offers(request, basket)
            discounts_after = basket.offer_applications

            # Look for discounts from this new voucher
            for discount in discounts_after:
                if discount['voucher'] and discount['voucher'] == voucher:
                    break
            else:
                basket.vouchers.remove(voucher)
                return Response(
                    {'reason': _(
                        "Your basket does not qualify for a voucher discount")},  # noqa
                    status=status.HTTP_406_NOT_ACCEPTABLE)

            ser = self.serializer_class(
                voucher, context={'request': request})
            return Response(ser.data)

        return Response(v_ser.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(('GET',))
def shipping_methods(request, format=None):
    """
    Get the available shipping methods and their cost for this order.

    GET:
    A list of shipping method details and the prices.
    """
    basket = operations.get_basket(request)
    shiping_methods = Repository().get_shipping_methods(
        basket=request.basket, user=request.user,
        request=request)
    ser = serializers.ShippingMethodSerializer(
        shiping_methods, many=True, context={'basket': basket})
    return Response(ser.data)


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
                "http://127.0.0.1:8000/oscarapi/stockrecords/100/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0"
        }
    """
    serializer_class = serializers.LineSerializer
    queryset = Line.objects.all()

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        if pk is not None:  # usually we need the lines of the basket
            basket = self.check_basket_permission(self.request, basket_pk=pk)
            prepped_basket = operations.assign_basket_strategy(
                basket, self.request)
            return prepped_basket.all_lines()
        elif self.request.user.is_staff:  # admin users can view a bit more
            return super(LineList, self).get_queryset()
        else:  # non admin users can view nothing at all here.
            return self.permission_denied(self.request)

    def get(self, request, pk=None, format=None):
        if pk is not None:
            basket = self.check_basket_permission(request, pk)
            prepped_basket = operations.assign_basket_strategy(basket, request)
            self.queryset = prepped_basket.all_lines()
            self.serializer_class = serializers.BasketLineSerializer

        return super(LineList, self).get(request, format)

    def post(self, request, pk=None, format=None):
        data_basket = self.get_data_basket(request.data, format)
        self.check_basket_permission(request, basket=data_basket)

        if pk is not None:
            url_basket = self.check_basket_permission(request, basket_pk=pk)
            if url_basket != data_basket:
                raise exceptions.NotAcceptable(
                    _('Target basket inconsistent %s != %s') % (
                        url_basket.pk, data_basket.pk
                    )
                )
        elif not request.user.is_staff:
            self.permission_denied(request)

        return super(LineList, self).post(request, format=format)


class LineDetail(PutIsPatchMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Line.objects.all()
    serializer_class = serializers.LineSerializer
    permission_classes = (permissions.IsAdminUserOrRequestContainsLine,)

    def get(self, request, pk=None, format=None):
        line = self.get_object()
        basket = operations.get_basket(request)

        # if the line is from the current basket, use the serializer that
        # computes the prices by using the strategy.
        if line.basket == basket:
            operations.assign_basket_strategy(line.basket, request)
            ser = serializers.BasketLineSerializer(
                instance=line, context={'request': request})
            return Response(ser.data)

        return super(LineDetail, self).get(request, pk, format)


class BasketLineDetail(PutIsPatchMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Line.objects.all()
    serializer_class = serializers.BasketLineSerializer
    permission_classes = (permissions.IsAdminUserOrRequestContainsLine,)

    def get_queryset(self):
        basket_pk = self.kwargs.get('basket_pk')
        basket = get_object_or_404(operations.editable_baskets(), pk=basket_pk)
        prepped_basket = operations.prepare_basket(basket, self.request)
        if operations.request_contains_basket(self.request, prepped_basket):
            return prepped_basket.lines
        else:
            return self.queryset.none()
