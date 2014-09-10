from django.contrib import auth
from oscar.core.loading import get_model
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from commerceconnect import serializers
from commerceconnect import serializers


__all__ = ('BasketView',)

Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')
LineAttribute = get_model('basket', 'LineAttribute')
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')
User = auth.get_user_model()


class BasketView(APIView):
    def get(self, request, format=None):
        if request.user.is_authenticated():
            basket = Basket.get_user_basket(request.user)
        else:
            basket = Basket.get_anonymous_basket(request)

        basket.store_basket(request)
        ser = serializers.BasketSerializer(basket, context={'request': request})
        return Response(ser.data)
