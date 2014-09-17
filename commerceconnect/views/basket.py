from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model, get_class
from rest_framework import status, generics, exceptions
from rest_framework.decorators import api_view
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.response import Response
from rest_framework.views import APIView

from commerceconnect import serializers, permissions
from commerceconnect.views.utils import (apply_offers, get_basket)


__all__ = ('BasketView', 'LineList', 'LineDetail', 'add_product')

Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')
Applicator = get_class('offer.utils', 'Applicator')
Selector = get_class('partner.strategy', 'Selector')

selector = Selector()


class BasketView(APIView):
    """
    Api for retrieving a user's basket.
    
    GET:
    Retrieve your basket.
    """
    def get(self, request, format=None):
        basket = get_basket(request)
        ser = serializers.BasketSerializer(basket, context={'request': request})
        return Response(ser.data)


@api_view(('POST',))
def add_product(request, format=None):
    """
    Add a certain quantity of a product to the basket.
    
    POST(url, quantity)
    {
        "url": "http://testserver.org/commerceconnect/products/209/",
        "quantity": 6
    }
    
    NOT IMPLEMENTED: LineAttributes, which are references to catalogue.Option.
    To Implement make the serializer accept lists of option object, which look
    like this:
    {
        option: "http://testserver.org/commerceconnect/options/1/,
        value: "some value"
    },
    These should be passed to basket.add_product as a list of dictionaries.
    """
    p_ser = serializers.AddProductSerializer(data=request.DATA, context={'request': request})
    if p_ser.is_valid():
        basket = get_basket(request)
        basket.add_product(p_ser.object, quantity=p_ser.init_data.get('quantity'))

        apply_offers(request, basket)

        ser = serializers.BasketSerializer(basket, context={'request': request})
        return Response(ser.data)

    return Response(p_ser.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


class LineList(generics.ListCreateAPIView):
    """
    Api for adding lines to a basket.
    
    Permission will be checked,
    Regular users may only access their own basket,
    staff users may access any basket.
    
    GET:
    A list of basket lines.
    
    POST(basket, line_reference, product, stockrecord, quantity, price_currency, price_excl_tax, price_incl_tax):
    Add a line to the basket, example::

        {
            "basket": "http://127.0.0.1:8000/commerceconnect/baskets/100/", 
            "line_reference": "234_345", 
            "product": "http://127.0.0.1:8000/commerceconnect/products/209/", 
            "stockrecord": "http://127.0.0.1:8000/commerceconnect/stockrecords/100/", 
            "quantity": 3, 
            "price_currency": "EUR", 
            "price_excl_tax": "100.0", 
            "price_incl_tax": "121.0"
        }
    """
    queryset = Line.objects.all()
    serializer_class = serializers.LineSerializer
    # The permission class is mainly used to check Basket permission!
    permission_classes = (permissions.IsAdminUserOrRequestOwner,)

    def get(self, request, pk=None, format=None):
        if pk is not None:
            self._check_basket_permission(request, pk)
            self.queryset = self.queryset.filter(basket__id=pk)
        elif not request.user.is_staff:
            self.permission_denied(request)

        return super(LineList, self).get(request, format)

    def post(self, request, pk=None, format=None):
        data_basket = self._get_data_basket(request.DATA, format)
        self._check_basket_permission(request, basket=data_basket)

        if pk is not None:
            url_basket = self._check_basket_permission(request, basket_pk=pk)
            if url_basket != data_basket:
                raise exceptions.NotAcceptable(
                    _('Target basket inconsistent %s != %s') % (
                        url_basket.pk, data_basket.pk
                    )
                )
        elif not request.user.is_staff:
            self.permission_denied(request)

        return super(LineList, self).post(request, format=format)

    def _get_data_basket(self, DATA, format):
        "Parse basket from relation hyperlink"
        basket_parser = HyperlinkedRelatedField(
            view_name='basket-detail',
            queryset=Basket.open,
            format=format
        )
        try:
            basket_uri = DATA.get('basket')
            data_basket = basket_parser.from_native(basket_uri)
        except ValidationError as e:
            raise exceptions.NotAcceptable(e.messages)
        else:
            return data_basket

    def _check_basket_permission(self, request, basket_pk=None, basket=None):
        "Check if the user may access this basket"
        if basket is None:
            basket = generics.get_object_or_404(Basket.open, pk=basket_pk)
        self.check_object_permissions(request, basket)
        return basket
        


class LineDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Line.objects.all()
    serializer_class = serializers.LineSerializer
