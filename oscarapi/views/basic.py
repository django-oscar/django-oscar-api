import functools
import itertools

from django.contrib import auth
from oscar.core.loading import get_model, get_class
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .mixin import PutIsPatchMixin
from oscarapi import serializers, permissions
from oscarapi.apps.basket.utils import prepare_basket


Selector = get_class('partner.strategy', 'Selector')

__all__ = (
    'BasketList', 'BasketDetail',
    'LineAttributeList', 'LineAttributeDetail',
    'ProductList', 'ProductDetail',
    'ProductPrice', 'ProductAvailability',
    'StockRecordList', 'StockRecordDetail',
    'UserList', 'UserDetail',
    'OptionList', 'OptionDetail',
    'CountryList', 'CountryDetail',
)

Basket = get_model('basket', 'Basket')
LineAttribute = get_model('basket', 'LineAttribute')
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')
Option = get_model('catalogue', 'Option')
User = auth.get_user_model()
Country = get_model('address', 'Country')


# TODO: For all API's in this file, the permissions should be checked if they
# are sensible.
class CountryList(generics.ListAPIView):
    serializer_class = serializers.CountrySerializer
    model = Country


class CountryDetail(generics.RetrieveAPIView):
    serializer_class = serializers.CountrySerializer
    model = Country


class BasketList(generics.ListCreateAPIView):
    model = Basket
    serializer_class = serializers.BasketSerializer
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        qs = super(BasketList, self).get_queryset()
        return itertools.imap(
            functools.partial(prepare_basket, request=self.request), 
            qs)

class BasketDetail(PutIsPatchMixin, generics.RetrieveUpdateDestroyAPIView):
    model = Basket
    serializer_class = serializers.BasketSerializer
    permission_classes = (permissions.IsAdminUserOrRequestOwner,)
    
    def get_object(self, queryset=None):
        basket = super(BasketDetail, self).get_object(queryset)
        return prepare_basket(basket, self.request)

class LineAttributeList(generics.ListCreateAPIView):
    model = LineAttribute
    serializer_class = serializers.LineAttributeSerializer


class LineAttributeDetail(PutIsPatchMixin, generics.RetrieveAPIView):
    model = LineAttribute
    serializer_class = serializers.LineAttributeSerializer


class ProductList(generics.ListAPIView):
    model = Product
    serializer_class = serializers.ProductLinkSerializer


class ProductDetail(generics.RetrieveAPIView):
    model = Product
    serializer_class = serializers.ProductSerializer


class ProductPrice(APIView):

    def get(self, request, pk=None, format=None):
        product = Product.objects.get(id=pk)
        strategy = Selector().strategy(request=request, user=request.user)
        price = strategy.fetch_for_product(product).price
        ser = serializers.PriceSerializer(price,
                                          context={'request': request})
        return Response(ser.data)


class ProductAvailability(generics.RetrieveAPIView):
    model = Product
    serializer_class = serializers.ProductAvailabilitySerializer


class StockRecordList(generics.ListAPIView):
    model = StockRecord
    serializer_class = serializers.StockRecordSerializer

    def get(self, request, pk=None, *args, **kwargs):
        if pk is not None:
            self.queryset = self.get_queryset().filter(product__id=pk)

        return super(StockRecordList, self).get(request, *args, **kwargs)


class StockRecordDetail(generics.RetrieveAPIView):
    model = StockRecord
    serializer_class = serializers.StockRecordSerializer


class UserList(generics.ListAPIView):
    model = User
    serializer_class = serializers.UserSerializer
    permission_classes = (IsAdminUser,)


class UserDetail(generics.RetrieveAPIView):
    model = User
    serializer_class = serializers.UserSerializer
    permission_classes = (IsAdminUser,)


class OptionList(generics.ListAPIView):
    model = Option
    serializer_class = serializers.OptionSerializer


class OptionDetail(generics.RetrieveAPIView):
    model = Option
    serializer_class = serializers.OptionSerializer
