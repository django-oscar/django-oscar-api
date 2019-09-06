from django.core.exceptions import ValidationError

from oscar.core.loading import get_model

from oscarapi import permissions

from rest_framework import exceptions, generics
from rest_framework.relations import HyperlinkedRelatedField

__all__ = ("BasketPermissionMixin",)

Basket = get_model("basket", "Basket")


class QuerySetList(list):
    def __init__(self, some_list, queryset):
        super(QuerySetList, self).__init__(some_list)
        self.queryset = queryset

    @property
    def model(self):
        return self.queryset.model


def parse_basket_from_hyperlink(DATA, format):  # pylint: disable=redefined-builtin
    "Parse basket from relation hyperlink"
    basket_parser = HyperlinkedRelatedField(
        view_name="basket-detail", queryset=Basket.objects, format=format
    )
    try:
        basket_uri = DATA.get("basket")
        data_basket = basket_parser.to_internal_value(basket_uri)
    except ValidationError as e:
        raise exceptions.NotAcceptable(e.messages)
    else:
        return data_basket


class BasketPermissionMixin(object):
    """
    This mixins adds some methods that can be used to check permissions
    on a basket instance.
    """

    # The permission class is mainly used to check Basket permission!
    permission_classes = (permissions.RequestAllowsAccessTo,)

    def get_data_basket(self, DATA, format):  # pylint: disable=redefined-builtin
        return parse_basket_from_hyperlink(DATA, format)

    def check_basket_permission(self, request, basket_pk=None, basket=None):
        "Check if the user may access this basket"
        if basket is None:
            basket = generics.get_object_or_404(Basket.objects, pk=basket_pk)
        self.check_object_permissions(request, basket)
        return basket
