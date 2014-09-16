from oscar.core.loading import get_model, get_class


__all__ = ('BasketView', 'LineList', 'LineDetail', 'add_product')

Basket = get_model('basket', 'Basket')
Applicator = get_class('offer.utils', 'Applicator')
Selector = get_class('partner.strategy', 'Selector')

selector = Selector()

def apply_offers(request, basket):
    "Apply offers and discounts to cart"
    if not basket.is_empty:
        Applicator().apply(request, basket)


def get_basket(request):
    "Get basket from the request."
    if request.user.is_authenticated():
        basket = Basket.get_user_basket(request.user)
    else:
        basket = Basket.get_anonymous_basket(request)
        if basket is None:
            basket = Basket.open.create()
            basket.save()

    basket.strategy = selector.strategy(request=request, user=request.user)
    apply_offers(request, basket)

    basket.store_basket(request)
    return basket


