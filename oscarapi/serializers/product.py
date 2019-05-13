from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from oscarapi.utils.loading import get_api_classes, get_api_class
from oscarapi.utils.settings import overridable
from oscarapi.serializers.utils import (
    OscarModelSerializer,
    OscarHyperlinkedModelSerializer,
)
from oscar.core.loading import get_model

Product = get_model('catalogue', 'Product')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
ProductImage = get_model('catalogue', 'ProductImage')
Option = get_model('catalogue', 'Option')
Partner = get_model('partner', 'Partner')
ProductClass = get_model('catalogue', 'ProductClass')
AttributeValueField, CategoryField = get_api_classes(
    "serializers.fields",
    ["AttributeValueField", "CategoryField"]
)
StockRecordSerializer = get_api_class("serializers.basket", "StockRecordSerializer")

# ProductCategory = get_model('catalogue', 'ProductCategory')
# ProductAttribute = get_model('catalogue', 'ProductAttribute')
# AttributeOption = get_model('catalogue', 'AttributeOption')


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
    # this field is declared here because it can only be used in combination
    # with this serializer

    # we declare the product as write_only since this serializer is meant to be
    # used nested inside a product serializer.
    product = serializers.PrimaryKeyRelatedField(
        many=False, write_only=True, queryset=Product.objects)

    name = serializers.CharField(source="attribute.name", required=False)
    code = serializers.CharField(source="attribute.code")
    value = AttributeValueField()  # handles different attribute value types

    def validate(self, data):
        """
        Because we flatten the attribute in the json, we must reconstruct the
        attribute during validation (cleaning). 
        """
        validated_data = super(ProductAttributeValueSerializer, self).validate(data)
        validated_data["attribute"] = self.validate_attribute(
            validated_data["attribute"], validated_data["product"])

        return validated_data

    def validate_attribute(self, attribute, product):
        "reconstruct attribute from the attribute data"
        product_class = product.get_product_class()

        try:
            attributes = self.Meta.model.attribute.get_queryset()
            return attributes.get(
                code=attribute["code"],
                product_class=product_class
            )
        except ObjectDoesNotExist:
            error_dict = dict(attribute, product=product)
            raise serializers.ValidationError(
                "No attribute %(name)s with code=%(code)s on %(product)s, "
                "please define it in the product_class first." % error_dict
            )

    def save(self, **kwargs):
        """
        Since there is a unique contraint, sometimes we want to update instead
        of creating a new object (because an integrity error would occur due
        to the constraint on attribute and product). If instance is set, the
        update method will be used instead of the create method.
        """
        value = self.validated_data["value"]
        product = self.validated_data["product"]
        attribute = self.validated_data["attribute"]
        attribute.save_value(product, value)
        return product.attribute_values.get(attribute=attribute)

    class Meta:
        model = ProductAttributeValue
        fields = overridable(
            'OSCARAPI_PRODUCT_ATTRIBUTE_VALUE_FIELDS',
            default=('name', 'value', 'code', 'product'))


class ProductImageSerializer(OscarModelSerializer):
    product = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Product.objects)

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
    "Base class shared by admin and public serializer"
    attributes = ProductAttributeValueSerializer(
        many=True, required=False, source="attribute_values")
    categories = CategoryField(many=True, required=False)
    product_class = serializers.SlugRelatedField(slug_field="slug", queryset=ProductClass.objects)
    options = OptionSerializer(many=True, required=False)
    recommended_products = serializers.HyperlinkedRelatedField(
        view_name='product-detail', many=True, required=False,
        queryset=Product.objects.filter(structure__in=[Product.PARENT, Product.STANDALONE])
    )

    class Meta:
        model = Product


class PublicProductSerializer(BaseProductSerializer):
    "Serializer base class used for public products api"
    url = serializers.HyperlinkedIdentityField(view_name='product-detail')
    price = serializers.HyperlinkedIdentityField(view_name='product-price', read_only=True)
    availability = serializers.HyperlinkedIdentityField(
        view_name='product-availability', read_only=True)

    def get_field_names(self, declared_fields, info):
        """
        Override get_field_names to make sure that we are not getting errors
        for not including declared fields.
        """
        return super(PublicProductSerializer, self).get_field_names({}, info)


class ChildProductserializer(PublicProductSerializer):
    "Serializer for child products"
    parent = serializers.HyperlinkedRelatedField(
        view_name='product-detail', queryset=Product.objects.filter(structure=Product.PARENT))
    # the below fields can be filled from the parent product if enabled.
    images = ProductImageSerializer(many=True, required=False, source='parent.images')
    description = serializers.CharField(source='parent.description')

    class Meta(PublicProductSerializer.Meta):
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


class ProductSerializer(PublicProductSerializer):
    "Serializer for public api with strategy fields added for price and availability"
    url = serializers.HyperlinkedIdentityField(view_name='product-detail')
    price = serializers.HyperlinkedIdentityField(view_name='product-price', read_only=True)
    availability = serializers.HyperlinkedIdentityField(
        view_name='product-availability', read_only=True)

    images = ProductImageSerializer(many=True, required=False)
    children = ChildProductserializer(many=True, required=False)

    class Meta(PublicProductSerializer.Meta):
        fields = overridable(
            'OSCARAPI_PRODUCTDETAIL_FIELDS',
            default=(
                'url', 'upc', 'id', 'title', 'description', 'structure',
                'date_created', 'date_updated', 'recommended_products',
                'attributes', 'categories', 'product_class',
                'stockrecords', 'images', 'price', 'availability', 'options',
                'children'))


class ProductLinkSerializer(ProductSerializer):
    """
    Summary serializer for list view, listing all products.
    
    This serializer can be easily made to show any field on ``ProductSerializer``,
    just add fields to the ``OSCARAPI_PRODUCT_FIELDS`` setting.
    """
    class Meta(PublicProductSerializer.Meta):
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
