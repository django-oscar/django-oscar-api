from commerceconnect.utils import overridable, OscarModelSerializer
from django.contrib.auth import get_user_model
from oscar.core.loading import get_model
from rest_framework import serializers


Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')
LineAttribute = get_model('basket', 'LineAttribute')
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')
User = get_user_model()


class BasketSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Basket
        fields = overridable('CC_BASKET_FIELDS', default=['id', 'owner', 'status', 'vouchers', 'lines'])
    
    def get_validation_exclusions(self, instance=None):
        """
        This is needed because oscar declared the owner field as ``null=True``,
        but ``blank=False``. That means the validator will claim you can not
        leave this value set to None.
        """
        return super(BasketSerializer, self).get_validation_exclusions(instance) + ['owner']


class LineSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Line


class LineAttributeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LineAttribute


class ProductSerializer(OscarModelSerializer):
    class Meta:
        model = Product
    

class StockRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockRecord


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
