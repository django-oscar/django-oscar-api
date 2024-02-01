

from django.utils.translation import ugettext_lazy as _

from oscar.apps.basket import signals
from oscar.core.loading import get_model, get_class

from rest_framework import status, generics, exceptions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import authentication, permissions

from oscarapi import permissions
from oscarapi.basket import operations
from oscarapi.utils.loading import get_api_classes, get_api_class
from oscarapi.views.utils import BasketPermissionMixin
from oscarapi import permissions
from django.shortcuts import get_object_or_404, redirect


WishList = get_model('wishlists', 'WishList')
Product = get_model('catalogue', 'Product')

WishListSerializer = get_api_class("serializers.wishlist", "WishListSerializer")



class WishListListView(generics.ListAPIView):
    """
    Api for retrieving users wishlists.

    GET:
    """

    serializer_class = WishListSerializer
    queryset = WishList.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.wishlists.all()