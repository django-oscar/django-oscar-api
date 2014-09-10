from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from oscar.apps.basket.abstract_models import AbstractBasket as _AbstractBasket
from oscar.core.loading import is_model_registered


class AbstractBasket(_AbstractBasket):

    @classmethod
    def get_anonymous_basket(cls, request):
        """
        Get basket from session.
        """
        basket_id = request.session.get(settings.OSCAR_BASKET_COOKIE_OPEN)
        try:
            basket = cls.open.get(pk=basket_id)
        except cls.DoesNotExist:
            basket = None

        return basket

    @classmethod
    def get_user_basket(cls, user):
        """
        get basket for a user.
        """
        try:
            basket, __ = cls.open.get_or_create(owner=user)
        except cls.MultipleObjectsReturned:
            # Not sure quite how we end up here with multiple baskets.
            # We merge them and create a fresh one
            old_baskets = list(cls.open.filter(owner=user))
            basket = old_baskets[0]
            for other_basket in old_baskets[1:]:
                basket.merge(other_basket, add_quantities=False)

        return basket

    def store_basket(self, request):
        request.session[settings.OSCAR_BASKET_COOKIE_OPEN] = self.pk

    class Meta:
        abstract = True
        app_label = 'basket'
        verbose_name = _('Basket')
        verbose_name_plural = _('Baskets')


if not is_model_registered('basket', 'Basket'):
    class Basket(AbstractBasket):
        pass
