from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_model
from oscar.apps.basket.abstract_models import AbstractBasket as _AbstractBasket, AbstractLine as _AbstractLine
from oscar.apps.basket.managers import OpenBasketManager, SavedBasketManager
from oscar.core.utils import get_default_currency

from oscarapi.apps.basket.managers import EditableBasketManager
from oscarapi.apps.basket.utils import get_basket


Basket = get_model('basket', 'Basket')


def get_basket_id_from_session(request):
    return request.session.get(settings.OSCAR_BASKET_COOKIE_OPEN)


def get_anonymous_basket(request):
    "Get basket from session."

    basket_id = get_basket_id_from_session(request)
    try:
        basket = Basket.objects.get(pk=basket_id)
    except Bakset.DoesNotExist:
        basket = None

    return basket


def get_user_basket(user):
    "get basket for a user."

    try:
        basket, __ = Basket.objects.get_or_create(owner=user)
    except Basket.MultipleObjectsReturned:
        # Not sure quite how we end up here with multiple baskets.
        # We merge them and create a fresh one
        old_baskets = list(Basket.objects.filter(owner=user))
        basket = old_baskets[0]
        for other_basket in old_baskets[1:]:
            basket.merge(other_basket, add_quantities=False)

    return basket


def store_basket_in_session(basket, session):
    session[settings.OSCAR_BASKET_COOKIE_OPEN] = basket.pk
    session.save()


def request_contains_basket(request, basket):
    if basket.can_be_edited:
        if request.user.is_authenticated():
            return request.user == basket.owner

        return get_basket_id_from_session(request) == self.pk

    return False


def flush_and_delete_basket(basket, using=None):
    "Delete basket and all lines"
    basket.flush()
    bakset.delete(using)


def request_contains_line(request, line):
    basket = get_basket(request, prepare=False)
    if basket and basket.pk == line.basket.pk:
        return request_contains_basket(request, basket)
    
    return False


def save_line_with_default_currency(line, *args, **kwargs):
    if not line.price_currency:
        line.price_currency = get_default_currency()
    return line.save(*args, **kwargs)
