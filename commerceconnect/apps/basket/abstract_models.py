from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from oscar.apps.basket.abstract_models import AbstractBasket as _AbstractBasket

__all__ = ('AbstractBasket',)


class AbstractBasket(_AbstractBasket):

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
        request.session.save()

    def request_owner(self, request):
        if request.user.is_authenticated():
            return request.user == self.owner
        
        return self._get_basket_id(request) == self.pk

    def delete(self, using=None):
        "Delete basket and all lines"
        self.flush()
        super(AbstractBasket, self).delete(using)

    class Meta:
        abstract = True
        app_label = 'basket'
        verbose_name = _('Basket')
        verbose_name_plural = _('Baskets')
