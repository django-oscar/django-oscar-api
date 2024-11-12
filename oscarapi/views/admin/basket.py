# pylint: disable=W0632
import functools

from rest_framework import generics

from oscar.core.loading import get_model
from oscarapi.basket.operations import (
    assign_basket_strategy,
    editable_baskets,
    get_anonymous_basket,
    prepare_basket,
)

from oscarapi.utils.loading import get_api_class
from oscarapi.views.utils import QuerySetList

APIAdminPermission = get_api_class("permissions", "APIAdminPermission")
AdminBasketSerializer = get_api_class(
    "serializers.admin.basket", "AdminBasketSerializer")
Basket = get_model("basket", "Basket")


class BasketAdminList(generics.ListCreateAPIView):
    """
    List of all baskets for admin users
    """
    serializer_class = AdminBasketSerializer
    permission_classes = (APIAdminPermission,)

    queryset = editable_baskets()

    def get_queryset(self):
        qs = super(BasketAdminList, self).get_queryset()
        mapped_with_baskets = list(
            map(functools.partial(assign_basket_strategy, request=self.request), qs)
        )
        return QuerySetList(mapped_with_baskets, qs)


class BasketAdminDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = Basket.objects.all()
    serializer_class = AdminBasketSerializer
    permission_classes = (APIAdminPermission,)
