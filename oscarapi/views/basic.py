import functools

from django.contrib import auth

from oscar.core.loading import get_class, get_model

from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from six.moves import map

from oscarapi import permissions
from oscarapi.basket.operations import (
    assign_basket_strategy,
    editable_baskets,
    get_anonymous_basket,
    prepare_basket
)
from oscarapi.utils.loading import get_api_classes, get_api_class

from .mixin import PutIsPatchMixin
from .utils import QuerySetList

__all__ = (
    "BasketList",
    "BasketDetail",
    "LineAttributeDetail",
    "StockRecordList",
    "StockRecordDetail",
    "UserList",
    "UserDetail",
    "OptionList",
    "OptionDetail",
    "CountryList",
    "CountryDetail",
    "PartnerList",
    "PartnerDetail",
)

Basket = get_model("basket", "Basket")
LineAttribute = get_model("basket", "LineAttribute")
Product = get_model("catalogue", "Product")
StockRecord = get_model("partner", "StockRecord")
Option = get_model("catalogue", "Option")
User = auth.get_user_model()
Country = get_model("address", "Country")
Partner = get_model("partner", "Partner")
Range = get_model("offer", "Range")

Selector = get_class("partner.strategy", "Selector")
APIAdminPermission = get_api_class("permissions", "APIAdminPermission")
UserSerializer = get_api_class("serializers.login", "UserSerializer")
CountrySerializer = get_api_class("serializers.checkout", "CountrySerializer")
BasketSerializer, LineAttributeSerializer, StockRecordSerializer = get_api_classes(  # pylint: disable=unbalanced-tuple-unpacking
    "serializers.basket",
    ["BasketSerializer", "LineAttributeSerializer", "StockRecordSerializer"],
)
RangeSerializer, OptionSerializer, PartnerSerializer = get_api_classes(  # pylint: disable=unbalanced-tuple-unpacking
    "serializers.product", ["RangeSerializer", "OptionSerializer", "PartnerSerializer"]
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
    """
    Retrieve all baskets that belong to the current user.
    """
    serializer_class = BasketSerializer
    queryset = editable_baskets()
    permission_classes = (APIAdminPermission,)

    def get_queryset(self):
        qs = super(BasketList, self).get_queryset()
        if self.request.user.is_authenticated:
            qs = qs.filter(owner=self.request.user)
            mapped_with_baskets = list(
                map(functools.partial(assign_basket_strategy, request=self.request), qs)
            )
        else:  # anonymous users have max 1 basket.
            basket = get_anonymous_basket(self.request)
            mapped_with_baskets = [prepare_basket(basket, self.request)]

        return QuerySetList(mapped_with_baskets, qs)


class BasketDetail(PutIsPatchMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BasketSerializer
    permission_classes = (permissions.RequestAllowsAccessTo,)
    queryset = editable_baskets()

    def get_object(self):
        basket = super(BasketDetail, self).get_object()
        return assign_basket_strategy(basket, self.request)


class LineAttributeDetail(PutIsPatchMixin, generics.RetrieveUpdateAPIView):
    queryset = LineAttribute.objects.all()
    serializer_class = LineAttributeSerializer
    permission_classes = (permissions.IsAdminUserOrRequestAllowsAccessTo,)  # noqa


class StockRecordList(generics.ListAPIView):
    serializer_class = StockRecordSerializer
    queryset = StockRecord.objects.all()
    permission_classes = (IsAdminUser,)

    def get(self, request, pk=None, *args, **kwargs):  # pylint: disable=keyword-arg-before-vararg,arguments-differ
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
    permission_classes = (IsAdminUser,)


class PartnerDetail(generics.RetrieveAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer


class RangeList(generics.ListAPIView):
    queryset = Range.objects.all()
    serializer_class = RangeSerializer


class RangeDetail(generics.RetrieveAPIView):
    queryset = Range.objects.all()
    serializer_class = RangeSerializer
