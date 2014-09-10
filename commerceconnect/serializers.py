from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from oscar.core.loading import get_model

from commerceconnect.utils import OscarModelSerializer, overridable, OscarHyperlinkedModelSerializer


Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')
LineAttribute = get_model('basket', 'LineAttribute')
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')
User = get_user_model()


class BasketSerializer(serializers.HyperlinkedModelSerializer):
    lines = serializers.HyperlinkedIdentityField(view_name='basket-lines-list')

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


class ProductLinkSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = overridable('CC_PRODUCT_FIELDS', default=('url', 'id'))

class ProductSerializer(OscarModelSerializer):
    stockrecords = serializers.HyperlinkedIdentityField(view_name='product-stockrecord-list')

    class Meta:
        model = Product


class StockRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockRecord


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = overridable('CC_USER_FIELDS', ('username', 'id', 'date_joined',))


class LoginSerializer(serializers.Serializer):

    username = serializers.CharField(max_length=30, required=True)
    password = serializers.CharField(max_length=255, required=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'],
                                       password=attrs['password'])
        if user is None:
            raise serializers.ValidationError('invalid login')
        elif not user.is_active:
            raise serializers.ValidationError('Can not log in as inactive user')
        elif user.is_staff and overridable('CC_BLOCK_ADMIN_API_ACCESS', True):
            raise serializers.ValidationError('Staff users can not log in via the rest api')

        return attrs

    def restore_object(self, attrs, instance=None):
        return authenticate(username=attrs['username'],
                                       password=attrs['password'])
