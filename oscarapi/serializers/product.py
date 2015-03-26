from rest_framework import serializers

from oscarapi.utils import (
    OscarModelSerializer,
    overridable,
    OscarHyperlinkedModelSerializer,
    OscarStrategySerializer
)
from oscar.core.loading import get_model


Product = get_model('catalogue', 'Product')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
ProductImage = get_model('catalogue', 'ProductImage')
Category = get_model('catalogue', 'Category')


class ProductLinkSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = overridable('OSCARAPI_PRODUCT_FIELDS',
                             default=('url', 'id', 'title'))


class ProductAttributeValueSerializer(OscarModelSerializer):
    name = serializers.RelatedField(source="attribute")
    value = serializers.SerializerMethodField('get_value')

    def get_value(self, obj):
        return obj.value

    class Meta:
        model = ProductAttributeValue
        fields = ('name', 'value',)


class ProductAttributeSerializer(OscarModelSerializer):
    productattributevalue_set = ProductAttributeValueSerializer(many=True)

    class Meta:
        model = ProductAttribute
        fields = ('name', 'productattributevalue_set')


class ProductImageSerializer(OscarModelSerializer):
    class Meta:
        model = ProductImage


class ProductAvailabilitySerializer(OscarStrategySerializer):
    is_available_to_buy = serializers.BooleanField(
        source="info.availability.is_available_to_buy")
    num_available = serializers.IntegerField(
        source="info.availability.num_available")
    message = serializers.CharField(source="info.availability.message")


class ProductSerializer(OscarModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='product-detail')
    stockrecords = serializers.HyperlinkedIdentityField(
        view_name='product-stockrecord-list')
    attributes = ProductAttributeValueSerializer(many=True,
                                                 required=False,
                                                 source="attribute_values")
    categories = serializers.RelatedField(many=True)
    product_class = serializers.RelatedField()
    images = ProductImageSerializer(many=True)
    price = serializers.HyperlinkedIdentityField(view_name='product-price')
    availability = serializers.HyperlinkedIdentityField(
        view_name='product-availability')

    class Meta:
        model = Product
        fields = overridable(
            'OSCARAPI_PRODUCTDETAIL_FIELDS',
            default=('url', 'id', 'title', 'description',
                     'date_created', 'date_updated', 'recommended_products',
                     'attributes', 'stockrecords', 'images', 'price',
                     'availability'))


class AddProductSerializer(serializers.Serializer):
    """
    Serializes and validates an add to basket request.
    """
    quantity = serializers.IntegerField(default=1, required=True)
    url = serializers.HyperlinkedRelatedField(
        view_name='product-detail', queryset=Product.objects,
        required=True)

    class Meta:
        model = Product
        fields = ['quantity', 'url']

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            return instance

        return attrs['url']


class AddProductToWishListSerializer(serializers.Serializer):
    """
    Serializes and validates an add to wishlist request.
    """
    url = serializers.HyperlinkedRelatedField(
        view_name='product-detail', queryset=Product.objects,
        required=True)

    class Meta:
        model = Product
        fields = ['url']

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            return instance

        return attrs['url']


class CategorySerializer(OscarModelSerializer):
    """
    Product category serializer
    """

    class Meta:
        model = Category
