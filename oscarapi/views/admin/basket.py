# pylint: disable=W0632
import functools

from rest_framework import generics

from oscar.core.loading import get_model
from oscarapi.basket.operations import (
    assign_basket_strategy,
    editable_baskets,
)

from oscarapi.utils.loading import get_api_class
from oscarapi.views.utils import QuerySetList, CustomPageNumberPagination

APIAdminPermission = get_api_class("permissions", "APIAdminPermission")
AdminBasketSerializer = get_api_class(
    "serializers.admin.basket", "AdminBasketSerializer"
)
Basket = get_model("basket", "Basket")


class BasketAdminList(generics.ListCreateAPIView):
    """
    List of all baskets for admin users
    """

    serializer_class = AdminBasketSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (APIAdminPermission,)

    queryset = editable_baskets()

    def get_queryset(self):
        qs = super(BasketAdminList, self).get_queryset()
        qs = qs.order_by("-id")
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)

        if page is not None:
            mapped_with_baskets = list(
                map(
                    functools.partial(assign_basket_strategy, request=self.request),
                    page,
                )
            )
            serializer = self.get_serializer(mapped_with_baskets, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return QuerySetList(mapped_with_baskets, qs)


class BasketAdminDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = Basket.objects.all()
    serializer_class = AdminBasketSerializer
    permission_classes = (APIAdminPermission,)
