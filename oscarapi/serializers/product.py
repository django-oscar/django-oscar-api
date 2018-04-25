from rest_framework import serializers
from django.utils.translation import ugettext as _

from oscarapi.utils import (
    OscarModelSerializer,
    overridable,
    OscarHyperlinkedModelSerializer
)
from oscar.core.loading import get_model


Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
AttributeOption = get_model('catalogue', 'AttributeOption')
ProductImage = get_model('catalogue', 'ProductImage')
Option = get_model('catalogue', 'Option')
Partner = get_model('partner', 'Partner')


class PartnerSerializer(OscarModelSerializer):
    class Meta:
        model = Partner
        fields = '__all__'


class OptionSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Option
        fields = overridable('OSCARAPI_OPTION_FIELDS', default=(
            'url', 'id', 'name', 'code', 'type'
        ))


class ProductAttributeValueSerializer(OscarModelSerializer):
    name = serializers.CharField(source="attribute.name")
    code = serializers.CharField(source="attribute.code")
    value = serializers.SerializerMethodField()

    def get_value(self, obj):
        obj_type = obj.attribute.type
        if obj_type == ProductAttribute.OPTION:
            return obj.value.option
        elif obj_type == ProductAttribute.MULTI_OPTION:
            return obj.value.values_list('option', flat=True)
        elif obj_type == ProductAttribute.FILE:
            return obj.value.url
        elif obj_type == ProductAttribute.IMAGE:
            return obj.value.url
        elif obj_type == ProductAttribute.ENTITY:
            if hasattr(obj.value, 'json'):
                return obj.value.json()
            else:
                return _(
                    "%(entity)s has no json method, can not convert to json" % {
                        'entity': repr(obj.value)
                    }
                )

        # return the value as stored on ProductAttributeValue in the correct type
        return obj.value

    class Meta:
        model = ProductAttributeValue
        fields = overridable(
            'OSCARAPI_PRODUCT_ATTRIBUTE_VALUE_FIELDS',
            default=('name', 'value', 'code'))


class ProductAttributeSerializer(OscarModelSerializer):
    productattributevalue_set = ProductAttributeValueSerializer(many=True)

    class Meta:
        model = ProductAttribute
        fields = overridable(
            'OSCARAPI_PRODUCT_ATTRIBUTE_FIELDS',
            default=('name', 'productattributevalue_set'))


class ProductImageSerializer(OscarModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'


class AvailabilitySerializer(serializers.Serializer):
    is_available_to_buy = serializers.BooleanField()
    num_available = serializers.IntegerField(required=False)
    message = serializers.CharField()


class RecommmendedProductSerializer(OscarModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='product-detail')

    class Meta:
        model = Product
        fields = overridable(
            'OSCARAPI_RECOMMENDED_PRODUCT_FIELDS', default=('url',))


class BaseProductSerializer(OscarModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='product-detail')
    stockrecords = serializers.HyperlinkedIdentityField(
        view_name='product-stockrecord-list')
    attributes = ProductAttributeValueSerializer(
        many=True, required=False, source="attribute_values")
    categories = serializers.StringRelatedField(many=True, required=False)
    product_class = serializers.StringRelatedField(required=False)
    price = serializers.HyperlinkedIdentityField(view_name='product-price')
    availability = serializers.HyperlinkedIdentityField(
        view_name='product-availability')
    options = OptionSerializer(many=True, required=False)
    recommended_products = RecommmendedProductSerializer(
        many=True, required=False)

    def get_field_names(self, declared_fields, info):
        """
        Override get_field_names to make sure that we are not getting errors
        for not including declared fields.
        """
        return super(BaseProductSerializer, self).get_field_names({}, info)

    class Meta:
        model = Product


class ChildProductserializer(BaseProductSerializer):
    parent = serializers.HyperlinkedRelatedField(
        view_name='product-detail', queryset=Product.objects)
    # the below fields can be filled from the parent product if enabled.
    images = ProductImageSerializer(many=True, required=False, source='parent.images')
    description = serializers.CharField(source='parent.description')

    class Meta(BaseProductSerializer.Meta):
        fields = overridable(
            'OSCARAPI_CHILDPRODUCTDETAIL_FIELDS',
            default=(
                'url', 'upc', 'id', 'title', 'structure',
                # 'parent', 'description', 'images', are not included by default, but
                # easily enabled by overriding OSCARAPI_CHILDPRODUCTDETAIL_FIELDS
                # in your settings file
                'date_created', 'date_updated', 'recommended_products',
                'attributes', 'categories', 'product_class',
                'stockrecords', 'price', 'availability', 'options'))


class ProductSerializer(BaseProductSerializer):
    images = ProductImageSerializer(many=True, required=False)
    children = ChildProductserializer(many=True, required=False)

    class Meta(BaseProductSerializer.Meta):
        fields = overridable(
            'OSCARAPI_PRODUCTDETAIL_FIELDS',
            default=(
                'url', 'upc', 'id', 'title', 'description', 'structure',
                'date_created', 'date_updated', 'recommended_products',
                'attributes', 'categories', 'product_class',
                'stockrecords', 'images', 'price', 'availability', 'options',
                'children'))


class ProductLinkSerializer(ProductSerializer):
    class Meta(BaseProductSerializer.Meta):
        fields = overridable(
            'OSCARAPI_PRODUCT_FIELDS', default=(
                'url', 'id', 'upc', 'title'
            ))


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
        view_name='product-detail', queryset=Product.objects, required=True)
    options = OptionValueSerializer(many=True, required=False)

    class Meta:
        model = Product
