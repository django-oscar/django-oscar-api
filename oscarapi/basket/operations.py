"This module contains operation on baskets and lines"
from django.conf import settings

from oscar.core.loading import get_class, get_model
from oscar.core.utils import get_default_currency

__all__ = (
    "apply_offers",
    "assign_basket_strategy",
    "prepare_basket",
    "get_basket",
    "get_basket_id_from_session",
    "get_anonymous_basket",
    "get_user_basket",
    "store_basket_in_session",
    "flush_and_delete_basket",
    "request_allows_access_to",
    "save_line_with_default_currency",
)

Basket = get_model("basket", "Basket")
Line = get_model("basket", "Line")
LineAttribute = get_model("basket", "LineAttribute")
Applicator = get_class("offer.applicator", "Applicator")
Selector = None


def apply_offers(request, basket):
    "Apply offers and discounts to cart"
    basket.reset_offer_applications()
    if not basket.is_empty:
        Applicator().apply(basket, request.user, request)


def assign_basket_strategy(basket, request):
    # fixes too early import of Selector
    # TODO: check if this is still true, now the basket models nolonger
    #       require this module to be loaded.
    global Selector

    if hasattr(request, "strategy"):
        basket.strategy = request.strategy
    else:  # in management commands, the request might not be available.
        if Selector is None:
            Selector = get_class("partner.strategy", "Selector")
        basket.strategy = Selector().strategy(request=request, user=request.user)

    apply_offers(request, basket)

    return basket


def prepare_basket(basket, request):
    assign_basket_strategy(basket, request)
    store_basket_in_session(basket, request.session)
    return basket


def get_basket(request, prepare=True):
    "Get basket from the request."
    if request.user.is_authenticated:
        basket = get_user_basket(request.user)
    else:
        basket = get_anonymous_basket(request)
        if basket is None:
            basket = Basket.objects.create()
            basket.save()
    return prepare_basket(basket, request) if prepare else basket


def get_basket_id_from_session(request):
    return request.session.get(settings.OSCAR_BASKET_COOKIE_OPEN)


def editable_baskets():
    return Basket.objects.filter(status__in=Basket.editable_statuses)


def get_anonymous_basket(request):
    "Get basket from session."

    basket_id = get_basket_id_from_session(request)
    try:
        basket = Basket.open.get(pk=basket_id)
    except Basket.DoesNotExist:
        basket = None

    return basket


def get_user_basket(user):
    "get basket for a user."

    try:
        basket, __ = Basket.open.get_or_create(owner=user)
    except Basket.MultipleObjectsReturned:
        # Not sure quite how we end up here with multiple baskets.
        # We merge them and create a fresh one
        old_baskets = list(Basket.open.filter(owner=user))
        basket = old_baskets[0]
        for other_basket in old_baskets[1:]:
            basket.merge(other_basket, add_quantities=False)

    return basket


def store_basket_in_session(basket, session):
    session[settings.OSCAR_BASKET_COOKIE_OPEN] = basket.pk
    session.save()


def request_allows_access_to_basket(request, basket):
    if basket.can_be_edited:
        if request.user.is_authenticated:
            return request.user == basket.owner

        return get_basket_id_from_session(request) == basket.pk

    return False


def flush_and_delete_basket(basket, using=None):
    "Delete basket and all lines"
    basket.flush()
    basket.delete(using)


def request_allows_access_to(request, obj):
    if isinstance(obj, Basket):
        return request_allows_access_to_basket(request, obj)

    basket = get_basket(request, prepare=False)

    if isinstance(obj, Line):
        if basket and basket.pk == obj.basket.pk:
            return request_allows_access_to_basket(request, basket)

    elif isinstance(obj, LineAttribute):
        if basket and basket.pk == obj.line.basket.pk:
            return request_allows_access_to_basket(request, basket)

    return False


def save_line_with_default_currency(line, *args, **kwargs):
    if not line.price_currency:
        line.price_currency = get_default_currency()
    return line.save(*args, **kwargs)
