from django.core.exceptions import ValidationError
from oscar.core.loading import get_model
from rest_framework import generics, exceptions
from rest_framework.relations import HyperlinkedRelatedField

from oscarapi import permissions


__all__ = ('BasketPermissionMixin',)

Basket = get_model('basket', 'Basket')


class BasketPermissionMixin(object):
    """
    This mixins adds some methods that can be used to check permissions
    on a basket instance.
    """
    # The permission class is mainly used to check Basket permission!
    permission_classes = (permissions.IsAdminUserOrRequestContainsBasket,)

    def get_data_basket(self, DATA, format):
        "Parse basket from relation hyperlink"
        basket_parser = HyperlinkedRelatedField(
            view_name='basket-detail',
            queryset=Basket.objects,
            format=format
        )
        try:
            basket_uri = DATA.get('basket')
            data_basket = basket_parser.to_internal_value(basket_uri)
        except ValidationError as e:
            raise exceptions.NotAcceptable(e.messages)
        else:
            return data_basket

    def check_basket_permission(self, request, basket_pk=None, basket=None):
        "Check if the user may access this basket"
        if basket is None:
            basket = generics.get_object_or_404(Basket.objects, pk=basket_pk)
        self.check_object_permissions(request, basket)
        return basket
