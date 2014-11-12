from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from oscar.apps.basket.abstract_models import AbstractBasket as _AbstractBasket, AbstractLine as _AbstractLine
from oscar.apps.basket.managers import OpenBasketManager, SavedBasketManager

from commerceconnect.apps.basket.managers import EditableBasketManager
from commerceconnect.apps.basket.utils import get_basket


__all__ = ('AbstractBasket', 'AbstractLine')


class AbstractBasket(_AbstractBasket):

    # managers
    objects = models.Manager()
    open = OpenBasketManager()
    saved = SavedBasketManager()
    editable = EditableBasketManager()

    @classmethod
    def _get_basket_id(cls, request):
        return request.session.get(settings.OSCAR_BASKET_COOKIE_OPEN)

    @classmethod
    def get_anonymous_basket(cls, request):
        """
        Get basket from session.
        """
        basket_id = cls._get_basket_id(request)
        try:
            basket = cls.editable.get(pk=basket_id)
        except cls.DoesNotExist:
            basket = None

        return basket

    @classmethod
    def get_user_basket(cls, user):
        """
        get basket for a user.
        """
        try:
            basket, __ = cls.editable.get_or_create(owner=user)
        except cls.MultipleObjectsReturned:
            # Not sure quite how we end up here with multiple baskets.
            # We merge them and create a fresh one
            old_baskets = list(cls.editable.filter(owner=user))
            basket = old_baskets[0]
            for other_basket in old_baskets[1:]:
                basket.merge(other_basket, add_quantities=False)

        return basket

    def store_basket(self, request):
        request.session[settings.OSCAR_BASKET_COOKIE_OPEN] = self.pk
        request.session.save()

    def request_owner(self, request):
        if self.can_be_edited:
            if request.user.is_authenticated():
                return request.user == self.owner

            return self._get_basket_id(request) == self.pk

        return False

    def delete(self, using=None):
        "Delete basket and all lines"
        self.flush()
        super(AbstractBasket, self).delete(using)

    class Meta:
        abstract = True
        app_label = 'basket'
        verbose_name = _('Basket')
        verbose_name_plural = _('Baskets')


class AbstractLine(_AbstractLine):
    def request_owner(self, request):
        basket = get_basket(request, prepare=False)
        if basket and basket.pk == self.basket.pk:
            return basket.request_owner(request)
        
        return False

    class Meta:
        abstract = True
        app_label = 'basket'
        unique_together = ("basket", "line_reference")
        verbose_name = _('Basket line')
        verbose_name_plural = _('Basket lines')
