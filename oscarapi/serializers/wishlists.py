# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from oscar.core.loading import get_model

from oscarapi.utils import overridable, OscarModelSerializer


WishList = get_model('wishlists', 'WishList')
Line = get_model('wishlists', 'Line')


class WishListSerializer(serializers.HyperlinkedModelSerializer):
    lines = serializers.HyperlinkedIdentityField(view_name='wishlist-lines-list')

    class Meta:
        model = WishList


class WishListLineSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='wishlistline-detail')

    class Meta:
        model = Line


class AddProductFromWishListSerializer(serializers.Serializer):
    url = serializers.HyperlinkedRelatedField(
        view_name='wishlistline-detail', queryset=Line.objects,
        required=True)

    class Meta:
        model = Line
        fields = ['url']

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            return instance

        return attrs['url']