from rest_framework import serializers

from oscarapi.utils import (
    OscarModelSerializer,
    overridable,
    OscarHyperlinkedModelSerializer,
    OscarStrategySerializer
)
from oscar.core.loading import get_model


Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
ProductImage = get_model('catalogue', 'ProductImage')
Option = get_model('catalogue', 'Option')


class OptionSerializer(OscarHyperlinkedModelSerializer):

    class Meta:
        model = Option
        fields = overridable('OSCARAPI_OPTION_FIELDS', default=[
            'url', 'id', 'name', 'code', 'type'
        ])


class ProductLinkSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = overridable(
            'OSCARAPI_PRODUCT_FIELDS', default=(
                'url', 'id', 'title')
            )


class ProductAttributeValueSerializer(OscarModelSerializer):
    name = serializers.RelatedField(
        source="attribute", queryset=ProductAttribute.objects)
    value = serializers.SerializerMethodField('get_attributevalue')

    def get_attributevalue(self, obj):
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
    categories = serializers.RelatedField(
        many=True, queryset=ProductCategory.objects)
    product_class = serializers.RelatedField(
        queryset=ProductClass.objects)
    images = ProductImageSerializer(many=True)
    price = serializers.HyperlinkedIdentityField(view_name='product-price')
    availability = serializers.HyperlinkedIdentityField(
        view_name='product-availability')
    options = OptionSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = overridable(
            'OSCARAPI_PRODUCTDETAIL_FIELDS',
            default=(
                'url', 'id', 'title', 'description',
                'date_created', 'date_updated', 'recommended_products',
                'attributes', 'categories', 'product_class',
                'stockrecords', 'images', 'price', 'availability', 'options'))


class OptionValueSerializer(serializers.Serializer):
    option = serializers.HyperlinkedRelatedField(
        view_name='option-detail', queryset=Option.objects)
    value = serializers.CharField()


class AddProductSerializer(serializers.Serializer):
    """
    Serializes and validates an add to basket request.
    """
    quantity = serializers.IntegerField(required=True)
    url = serializers.HyperlinkedRelatedField(
        view_name='product-detail', queryset=Product.objects,
        required=True)
    options = OptionValueSerializer(many=True, required=False)

    class Meta:
        model = Product
