from django.utils.translation import ugettext_lazy as _

from oscar.apps.basket import signals
from oscar.core.loading import get_model

from rest_framework import status, generics, exceptions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from oscarapi import serializers, permissions
from oscarapi.basket.operations import (
    apply_offers,
    get_basket
)
from oscarapi.views.mixin import PutIsPatchMixin
from oscarapi.views.utils import BasketPermissionMixin


__all__ = ('BasketView', 'LineList', 'LineDetail', 'AddProductView',
           'add_voucher')

Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')


class BasketView(APIView):
    """
    Api for retrieving a user's basket.

    GET:
    Retrieve your basket.
    """
    def get(self, request, format=None):
        basket = get_basket(request)
        ser = serializers.BasketSerializer(basket,
                                           context={'request': request})
        return Response(ser.data)


class AddProductView(APIView):

    def validate(self, basket, product, quantity):
        availability = basket.strategy.fetch_for_product(
            product).availability

        # check if product is available at all
        if not availability.is_available_to_buy:
            return False, availability.reason

        # check if we can buy this quantity
        allowed, message = availability.is_purchase_permitted(quantity)
        if not allowed:
            return False, message

        # check if there is a limit on amount
        allowed, message = basket.is_quantity_allowed(quantity)
        if not allowed:
            return False, quantity

        return True, ""

    def post(self, request, format=None):
        """
        Add a certain quantity of a product to the basket.

        POST(url, quantity)
        {
            "url": "http://testserver.org/commerceconnect/products/209/",
            "quantity": 6
        }

        NOT IMPLEMENTED: LineAttributes, which are references to
        catalogue.Option. To Implement make the serializer accept lists
        of option object, which look like this:
        {
            option: "http://testserver.org/commerceconnect/options/1/,
            value: "some value"
        },
        These should be passed to basket.add_product as a list of dictionaries.
        """
        p_ser = serializers.AddProductSerializer(
            data=request.DATA, context={'request': request})
        if p_ser.is_valid():
            basket = get_basket(request)
            product = p_ser.object
            quantity = p_ser.init_data.get('quantity')

            basket_valid, message = self.validate(basket, product, quantity)
            if not basket_valid:
                return Response(
                    {'reason': message},
                    status=status.HTTP_406_NOT_ACCEPTABLE)

            basket.add_product(product, quantity=quantity)
            apply_offers(request, basket)
            ser = serializers.BasketSerializer(
                basket,  context={'request': request})
            return Response(ser.data)

        return Response(
            {'reason': p_ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(('POST',))
def add_voucher(request, format=None):
    """
    Add a voucher to the basket.
    
    POST(vouchercode)
    {
        "vouchercode": "kjadjhgadjgh7667"
    }
    
    Will return 200 and the voucher as json if succesful.
    If unsuccessful, will return 406 with the error.
    """
    v_ser = serializers.VoucherAddSerializer(data=request.DATA,
                                             context={'request': request})
    if v_ser.is_valid():
        basket = get_basket(request)
        voucher = v_ser.object
        basket.vouchers.add(voucher)

        signals.voucher_addition.send(
            sender=None, basket=basket, voucher=voucher)
        
        # Recalculate discounts to see if the voucher gives any
        apply_offers(request, basket)
        discounts_after = basket.offer_applications

        # Look for discounts from this new voucher
        for discount in discounts_after:
            if discount['voucher'] and discount['voucher'] == voucher:
                break
        else:
            basket.vouchers.remove(voucher)
            return Response({'reason':_("Your basket does not qualify for a voucher discount")}, status=status.HTTP_406_NOT_ACCEPTABLE)

        ser = serializers.VoucherSerializer(voucher, context={'request': request})
        return Response(ser.data)

    return Response(v_ser.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


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
    queryset = Line.objects.all()
    serializer_class = serializers.LineSerializer

    def get(self, request, pk=None, format=None):
        if pk is not None:
            self.check_basket_permission(request, pk)
            self.queryset = self.queryset.filter(basket__id=pk)
        elif not request.user.is_staff:
            self.permission_denied(request)

        return super(LineList, self).get(request, format)

    def post(self, request, pk=None, format=None):
        data_basket = self.get_data_basket(request.DATA, format)
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
