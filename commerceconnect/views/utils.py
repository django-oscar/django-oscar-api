from django.core.exceptions import ValidationError
from oscar.core.loading import get_model, get_class
from rest_framework import generics, exceptions
from rest_framework.relations import HyperlinkedRelatedField

from commerceconnect import permissions


__all__ = ('prepare_basket', 'get_basket', 'apply_offers', 'BasketPermissionMixin')

Basket = get_model('basket', 'Basket')
Applicator = get_class('offer.utils', 'Applicator')
Selector = get_class('partner.strategy', 'Selector')

selector = Selector()

def apply_offers(request, basket):
    "Apply offers and discounts to cart"
    if not basket.is_empty:
        Applicator().apply(request, basket)


def prepare_basket(basket, request):
    basket.strategy = selector.strategy(request=request, user=request.user)
    apply_offers(request, basket)

    basket.store_basket(request)
    return basket


def get_basket(request):
    "Get basket from the request."
    if request.user.is_authenticated():
        basket = Basket.get_user_basket(request.user)
    else:
        basket = Basket.get_anonymous_basket(request)
        if basket is None:
            basket = Basket.open.create()
            basket.save()

    return prepare_basket(basket, request)


class BasketPermissionMixin(object):
    """
    This mixins adds some methods that can be used to check permissions
    on a basket instance.
    """
    # The permission class is mainly used to check Basket permission!
    permission_classes = (permissions.IsAdminUserOrRequestOwner,)

    def get_data_basket(self, DATA, format):
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

    def check_basket_permission(self, request, basket_pk=None, basket=None):
        "Check if the user may access this basket"
        if basket is None:
            basket = generics.get_object_or_404(Basket.open, pk=basket_pk)
        self.check_object_permissions(request, basket)
        return basket

