from copy import deepcopy
from rest_framework import serializers
from rest_framework.fields import empty

from oscarapi.utils.loading import get_api_classes, get_api_class
from oscarapi.utils.settings import overridable
from oscarapi.utils.files import file_hash
from oscarapi.serializers.utils import (
    OscarModelSerializer,
    OscarHyperlinkedModelSerializer,
    UpdateListSerializer,
    UpdateForwardManyToManySerializer,
)
from oscar.core.loading import get_model

from .exceptions import FieldError

Product = get_model("catalogue", "Product")
Range = get_model("offer", "Range")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
ProductImage = get_model("catalogue", "ProductImage")
Option = get_model("catalogue", "Option")
Partner = get_model("partner", "Partner")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")
Category = get_model("catalogue", "Category")
AttributeOption = get_model("catalogue", "AttributeOption")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeValueField, CategoryField = get_api_classes(  # pylint: disable=unbalanced-tuple-unpacking
    "serializers.fields", ["AttributeValueField", "CategoryField"]
)
StockRecordSerializer = get_api_class("serializers.basket", "StockRecordSerializer")


class AttributeOptionGroupSerializer(OscarHyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="admin-attributeoptiongroup-detail"
    )
    options = serializers.SlugRelatedField(
        many=True,
        required=True,
        slug_field="option",
        queryset=AttributeOption.objects.get_queryset(),
    )

    class Meta:
        model = AttributeOptionGroup
        fields = "__all__"


class CategorySerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductAttributeSerializer(OscarHyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="admin-productattribute-detail"
    )
    product_class = serializers.SlugRelatedField(
        slug_field="slug", queryset=ProductClass.objects.get_queryset()
    )
    option_group = AttributeOptionGroupSerializer(required=False)

    class Meta:
        model = ProductAttribute
        fields = "__all__"


class RangeSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Range
        fields = "__all__"


class PartnerSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Partner
        fields = "__all__"


class OptionSerializer(OscarHyperlinkedModelSerializer):
    code = serializers.SlugField()

    class Meta:
        model = Option
        fields = overridable("OSCARAPI_OPTION_FIELDS", default="__all__")
        list_serializer_class = UpdateForwardManyToManySerializer


class ProductAttributeValueListSerializer(UpdateListSerializer):
    def get_value(self, dictionary):
        values = super(ProductAttributeValueListSerializer, self).get_value(dictionary)
        if values is empty:
            return values

        product_class = dictionary.get("product_class")
        return [dict(value, product_class=product_class) for value in values]


class ProductAttributeValueSerializer(OscarModelSerializer):
    # we declare the product as write_only since this serializer is meant to be
    # used nested inside a product serializer.
    product = serializers.PrimaryKeyRelatedField(
        many=False, write_only=True, required=False, queryset=Product.objects
    )

    value = AttributeValueField()  # handles different attribute value types
    # while code is specified as read_only, it is still required, because otherwise
    # the attribute is unknown, so while it will never be overwritten, you do
    # have to include it in your data structure
    code = serializers.CharField(source="attribute.code", read_only=True)
    name = serializers.CharField(
        source="attribute.name", required=False, read_only=True
    )

    def to_internal_value(self, data):
        try:
            internal_value = super(
                ProductAttributeValueSerializer, self
            ).to_internal_value(data)
            internal_value["product_class"] = data.get("product_class")
            return internal_value
        except FieldError as e:
            raise serializers.ValidationError(e.detail)

    def save(self, **kwargs):
        """
        Since there is a unique contraint, sometimes we want to update instead
        of creating a new object (because an integrity error would occur due
        to the constraint on attribute and product). If instance is set, the
        update method will be used instead of the create method.
        """
        data = deepcopy(kwargs)
        data.update(self.validated_data)
        return self.update_or_create(data)

    def update_or_create(self, validated_data):
        value = validated_data["value"]
        product = validated_data["product"]
        attribute = validated_data["attribute"]
        attribute.save_value(product, value)
        return product.attribute_values.get(attribute=attribute)

    create = update_or_create

    def update(self, instance, validated_data):
        data = deepcopy(validated_data)
        data["product"] = instance.product
        return self.update_or_create(data)

    class Meta:
        model = ProductAttributeValue
        list_serializer_class = ProductAttributeValueListSerializer
        fields = overridable(
            "OSCARAPI_PRODUCT_ATTRIBUTE_VALUE_FIELDS",
            default=("name", "value", "code", "product"),
        )


class ProductImageUpdateListSerializer(UpdateListSerializer):
    "Select existing image based on hash of image content"

    def select_existing_item(self, manager, datum):
        # determine the hash of the passed image
        target_file_hash = file_hash(datum["original"])
        for image in manager.all():  # search for a match in the set of exising images
            _hash = file_hash(image.original)
            if _hash == target_file_hash:
                # django will create a copy of the original under a weird name,
                # because the image is freshly fetched, except if we use the
                # original image FileObject
                datum["original"] = image.original
                return image

        return None


class ProductImageSerializer(OscarModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, queryset=Product.objects
    )

    class Meta:
        model = ProductImage
        fields = "__all__"
        list_serializer_class = ProductImageUpdateListSerializer


class AvailabilitySerializer(serializers.Serializer):  # pylint: disable=abstract-method
    is_available_to_buy = serializers.BooleanField()
    num_available = serializers.IntegerField(required=False)
    message = serializers.CharField()


class RecommmendedProductSerializer(OscarModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")

    class Meta:
        model = Product
        fields = overridable("OSCARAPI_RECOMMENDED_PRODUCT_FIELDS", default=("url",))


class BaseProductSerializer(OscarModelSerializer):
    "Base class shared by admin and public serializer"
    attributes = ProductAttributeValueSerializer(
        many=True, required=False, source="attribute_values"
    )
    categories = CategoryField(many=True, required=False)
    product_class = serializers.SlugRelatedField(
        slug_field="slug", queryset=ProductClass.objects
    )
    options = OptionSerializer(many=True, required=False)
    recommended_products = serializers.HyperlinkedRelatedField(
        view_name="product-detail",
        many=True,
        required=False,
        queryset=Product.objects.filter(
            structure__in=[Product.PARENT, Product.STANDALONE]
        ),
    )

    class Meta:
        model = Product


class PublicProductSerializer(BaseProductSerializer):
    "Serializer base class used for public products api"
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")
    price = serializers.HyperlinkedIdentityField(
        view_name="product-price", read_only=True
    )
    availability = serializers.HyperlinkedIdentityField(
        view_name="product-availability", read_only=True
    )

    def get_field_names(self, declared_fields, info):
        """
        Override get_field_names to make sure that we are not getting errors
        for not including declared fields.
        """
        return super(PublicProductSerializer, self).get_field_names({}, info)


class ChildProductserializer(PublicProductSerializer):
    "Serializer for child products"
    parent = serializers.HyperlinkedRelatedField(
        view_name="product-detail",
        queryset=Product.objects.filter(structure=Product.PARENT),
    )
    # the below fields can be filled from the parent product if enabled.
    images = ProductImageSerializer(many=True, required=False, source="parent.images")
    description = serializers.CharField(source="parent.description")

    class Meta(PublicProductSerializer.Meta):
        fields = overridable(
            "OSCARAPI_CHILDPRODUCTDETAIL_FIELDS",
            default=(
                "url",
                "upc",
                "id",
                "title",
                "structure",
                # 'parent', 'description', 'images', are not included by default, but
                # easily enabled by overriding OSCARAPI_CHILDPRODUCTDETAIL_FIELDS
                # in your settings file
                "date_created",
                "date_updated",
                "recommended_products",
                "attributes",
                "categories",
                "product_class",
                "stockrecords",
                "price",
                "availability",
                "options",
            ),
        )


class ProductSerializer(PublicProductSerializer):
    "Serializer for public api with strategy fields added for price and availability"
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")
    price = serializers.HyperlinkedIdentityField(
        view_name="product-price", read_only=True
    )
    availability = serializers.HyperlinkedIdentityField(
        view_name="product-availability", read_only=True
    )

    images = ProductImageSerializer(many=True, required=False)
    children = ChildProductserializer(many=True, required=False)

    class Meta(PublicProductSerializer.Meta):
        fields = overridable(
            "OSCARAPI_PRODUCTDETAIL_FIELDS",
            default=(
                "url",
                "upc",
                "id",
                "title",
                "description",
                "structure",
                "date_created",
                "date_updated",
                "recommended_products",
                "attributes",
                "categories",
                "product_class",
                "stockrecords",
                "images",
                "price",
                "availability",
                "options",
                "children",
            ),
        )


class ProductLinkSerializer(ProductSerializer):
    """
    Summary serializer for list view, listing all products.
    
    This serializer can be easily made to show any field on ``ProductSerializer``,
    just add fields to the ``OSCARAPI_PRODUCT_FIELDS`` setting.
    """

    class Meta(PublicProductSerializer.Meta):
        fields = overridable(
            "OSCARAPI_PRODUCT_FIELDS", default=("url", "id", "upc", "title")
        )


class OptionValueSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    option = serializers.HyperlinkedRelatedField(
        view_name="option-detail", queryset=Option.objects
    )
    value = serializers.CharField()


class AddProductSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializes and validates an add to basket request.
    """

    quantity = serializers.IntegerField(required=True)
    url = serializers.HyperlinkedRelatedField(
        view_name="product-detail", queryset=Product.objects, required=True
    )
    options = OptionValueSerializer(many=True, required=False)

    class Meta:
        model = Product
