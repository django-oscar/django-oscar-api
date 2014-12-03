from rest_framework import serializers

from commerceconnect.utils import (
    OscarModelSerializer,
    overridable,
    OscarHyperlinkedModelSerializer
)
from oscar.core.loading import get_model


Product = get_model('catalogue', 'Product')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')


class ProductLinkSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = overridable('CC_PRODUCT_FIELDS', default=('url',
                                                           'id',
                                                           'title'))


class ProductAttributeValueSerializer(OscarModelSerializer):
    attribute = serializers.RelatedField()
    value = serializers.SerializerMethodField('get_value')

    def get_value(self, obj):
        return obj.value

    class Meta:
        model = ProductAttributeValue
        fields = ('attribute', 'value',)


class ProductAttributeSerializer(OscarModelSerializer):
    productattributevalue_set = ProductAttributeValueSerializer(many=True)

    class Meta:
        model = ProductAttribute
        fields = ('name', 'productattributevalue_set')


class ProductSerializer(OscarModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='product-detail')
    stockrecords = serializers.HyperlinkedIdentityField(
        view_name='product-stockrecord-list')
    attributes = ProductAttributeValueSerializer(many=True,
                                                 required=False,
                                                 source="attribute_values")
    categories = serializers.RelatedField(many=True)
    product_class = serializers.RelatedField()

    class Meta:
        model = Product
        fields = overridable(
            'CC_PRODUCTDETAIL_FIELDS',
            default=('url', 'id', 'title', 'description',
                     'date_created', 'date_updated', 'recommended_products',
                     'attributes', 'stockrecords'))


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
