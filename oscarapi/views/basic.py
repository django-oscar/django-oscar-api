import functools

from django.contrib import auth

from oscar.core.loading import get_class, get_classes, get_model

from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from six.moves import map

from oscarapi import permissions, serializers
from oscarapi.basket.operations import assign_basket_strategy
from oscarapi.utils.loading import get_api_classes, get_api_class

from .mixin import PutIsPatchMixin


__all__ = (
    'BasketList', 'BasketDetail',
    'LineAttributeList', 'LineAttributeDetail',
    'StockRecordList', 'StockRecordDetail',
    'UserList', 'UserDetail',
    'OptionList', 'OptionDetail',
    'CountryList', 'CountryDetail',
    'PartnerList', 'PartnerDetail',
)

Basket = get_model('basket', 'Basket')
LineAttribute = get_model('basket', 'LineAttribute')
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')
Option = get_model('catalogue', 'Option')
User = auth.get_user_model()
Country = get_model('address', 'Country')
Partner = get_model('partner', 'Partner')

Selector = get_class('partner.strategy', 'Selector')
UserSerializer = get_api_class("serializers.login", "UserSerializer")
CountrySerializer = get_api_class("serializers.checkout", "CountrySerializer")
BasketSerializer, LineAttributeSerializer, StockRecordSerializer = get_api_classes(
    "serializers.basket", [
        "BasketSerializer",
        "LineAttributeSerializer",
        "StockRecordSerializer"
    ],
)
OptionSerializer, PartnerSerializer = get_api_classes(
    "serializers.product", ["OptionSerializer", "PartnerSerializer"]
)

# TODO: For all API's in this file, the permissions should be checked if they
# are sensible.
class CountryList(generics.ListAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects.all()


class CountryDetail(generics.RetrieveAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects.all()


class BasketList(generics.ListCreateAPIView):
    serializer_class = BasketSerializer
    queryset = Basket.objects.all()
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        qs = super(BasketList, self).get_queryset()
        return list(map(
            functools.partial(assign_basket_strategy, request=self.request),
            qs))


class BasketDetail(PutIsPatchMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BasketSerializer
    permission_classes = (permissions.IsAdminUserOrRequestAllowsAccessTo,)
    queryset = Basket.objects.all()

    def get_object(self):
        basket = super(BasketDetail, self).get_object()
        return assign_basket_strategy(basket, self.request)


class LineAttributeList(generics.ListCreateAPIView):
    queryset = LineAttribute.objects.all()
    serializer_class = LineAttributeSerializer


class LineAttributeDetail(PutIsPatchMixin, generics.RetrieveUpdateAPIView):
    queryset = LineAttribute.objects.all()
    serializer_class = LineAttributeSerializer
    permission_classes = (permissions.IsAdminUserOrRequestAllowsAccessTo,)  # noqa


class StockRecordList(generics.ListAPIView):
    serializer_class = StockRecordSerializer
    queryset = StockRecord.objects.all()

    def get(self, request, pk=None, *args, **kwargs):
        if pk is not None:
            self.queryset = self.queryset.filter(product__id=pk)

        return super(StockRecordList, self).get(request, *args, **kwargs)


class StockRecordDetail(generics.RetrieveAPIView):
    queryset = StockRecord.objects.all()
    serializer_class = StockRecordSerializer


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)


class OptionList(generics.ListAPIView):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer


class OptionDetail(generics.RetrieveAPIView):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer


class PartnerList(generics.ListAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer


class PartnerDetail(generics.RetrieveAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
