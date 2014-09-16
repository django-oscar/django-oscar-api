from django.contrib.auth import get_user_model, authenticate
from oscar.core.loading import get_model
from rest_framework import serializers

from commerceconnect.utils import OscarModelSerializer, overridable, OscarHyperlinkedModelSerializer


Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')
LineAttribute = get_model('basket', 'LineAttribute')
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')
Option = get_model('catalogue', 'Option')
User = get_user_model()


class BasketSerializer(serializers.HyperlinkedModelSerializer):
    lines = serializers.HyperlinkedIdentityField(view_name='basket-lines-list')
    offer_applications = serializers.SerializerMethodField('get_offer_applications')

    class Meta:
        model = Basket
        fields = overridable('CC_BASKET_FIELDS', default=['id', 'owner', 'status', 'vouchers', 'lines', 'url', 'offer_applications'])
    
    def get_validation_exclusions(self, instance=None):
        """
        This is needed because oscar declared the owner field as ``null=True``,
        but ``blank=False``. That means the validator will claim you can not
        leave this value set to None.
        """
        return super(BasketSerializer, self).get_validation_exclusions(instance) + ['owner']

    def get_offer_applications(self, obj):
        if hasattr(obj, 'offer_applications'):
            return obj.offer_applications.offers
        return {}


class LineAttributeSerializer(serializers.HyperlinkedModelSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(LineAttributeSerializer, self).__init__(*args, **kwargs)
        if fields:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
    class Meta:
        model = LineAttribute


class LineSerializer(serializers.HyperlinkedModelSerializer):
    attributes = LineAttributeSerializer(many=True, fields=('url', 'option', 'value'), required=False)

    class Meta:
        model = Line


class ProductLinkSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = overridable('CC_PRODUCT_FIELDS', default=('url', 'id'))

class ProductSerializer(OscarModelSerializer):
    stockrecords = serializers.HyperlinkedIdentityField(view_name='product-stockrecord-list')
    url = serializers.HyperlinkedIdentityField(view_name='product-detail')

    class Meta:
        model = Product


class OptionSerializer(OscarModelSerializer):

    class Meta:
        model = Option


class AddProductSerializer(serializers.Serializer):
    """
    Serializes and validates an add to basket request.
    """
    quantity = serializers.IntegerField(default=1, required=True)
    url = serializers.URLField(required=True)

    class Meta:
        model = Product
        fields = ['quantity', 'url']

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            return instance

        product_url_parser = serializers.HyperlinkedRelatedField(
            view_name='product-detail',
            queryset=Product.objects,
        )

        return product_url_parser.from_native(attrs.get('url'))


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
