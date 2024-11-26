import logging
from decimal import Decimal

from django.utils.translation import ugettext as _
from django.contrib.auth import get_user_model
from rest_framework import serializers

from oscar.core.loading import get_model

from oscarapi.basket import operations
from oscarapi.utils.settings import overridable
from oscarapi.serializers.fields import (
    DrillDownHyperlinkedIdentityField,
    DrillDownHyperlinkedRelatedField,
)
from oscarapi.serializers.utils import (
    OscarModelSerializer,
    OscarHyperlinkedModelSerializer,
    UpdateListSerializer
)
from oscarapi.serializers.fields import TaxIncludedDecimalField
from datetime import datetime, date


logger = logging.getLogger(__name__)


WishList = get_model('wishlists', 'WishList')
Line = get_model('wishlists', 'Line')


class WishlistLineSerializer(serializers.ModelSerializer):
    "Serializer for WishLists Lines of loggined user"

    class Meta:
        model = Line
        fields = '__all__'


class WishListSerializer(serializers.ModelSerializer):
    "Serializer for WishLists of loggined user"
    lines = WishlistLineSerializer(many=True)

    class Meta:
        model = WishList
        fields = '__all__'