from django.contrib import auth
from oscar.core.loading import get_model, get_class
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from commerceconnect import serializers


__all__ = ('BasketView',)

Basket = get_model('basket', 'Basket')
Applicator = get_class('offer.utils', 'Applicator')
Selector = get_class('partner.strategy', 'Selector')

selector = Selector()


class BasketView(APIView):
    """
    Api for retrieving a user's basket.
    
    GET:
    Retrieve your basket.
    """
    def get(self, request, format=None):
        if request.user.is_authenticated():
            basket = Basket.get_user_basket(request.user)
        else:
            basket = Basket.get_anonymous_basket(request)
            if basket is None:
                basket = Basket()
                basket.save()

        basket.strategy = selector.strategy(request=request, user=request.user)
        self.apply_offers(request, basket)

        basket.store_basket(request)
        
        ser = serializers.BasketSerializer(basket, context={'request': request})
        return Response(ser.data)

    def apply_offers(self, request, basket):
        if not basket.is_empty:
            Applicator().apply(request, basket)
