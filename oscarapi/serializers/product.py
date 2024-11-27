# pylint: disable=W0632

import logging
from copy import deepcopy
from django.db.models.manager import Manager
from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework.fields import empty

from oscar.core.loading import get_model

from oscarapi.utils.exists import bound_unique_together_get_or_create_multiple
from oscarapi.utils.loading import get_api_classes
from oscarapi import settings
from oscarapi.utils.files import file_hash
from oscarapi.utils.exists import find_existing_attribute_option_group
from oscarapi.utils.accessors import getitems
from oscarapi.serializers.fields import DrillDownHyperlinkedIdentityField
from oscarapi.utils.attributes import AttributeConverter
from oscarapi.serializers.utils import (
    OscarModelSerializer,
    OscarHyperlinkedModelSerializer,
    UpdateListSerializer,
    UpdateForwardManyToManySerializer,
)

from .exceptions import FieldError

logger = logging.getLogger(__name__)
Product = get_model("catalogue", "Product")
Range = get_model("offer", "Range")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
ProductImage = get_model("catalogue", "ProductImage")
Option = get_model("catalogue", "Option")
Partner = get_model("partner", "Partner")
StockRecord = get_model("partner", "StockRecord")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")
Category = get_model("catalogue", "Category")
AttributeOption = get_model("catalogue", "AttributeOption")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeValueField, CategoryField, SingleValueSlugRelatedField = get_api_classes(
    "serializers.fields",
    ["AttributeValueField", "CategoryField", "SingleValueSlugRelatedField"],
)


class AttributeOptionGroupSerializer(OscarHyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="admin-attributeoptiongroup-detail"
    )
    options = SingleValueSlugRelatedField(
        many=True,
        required=True,
        slug_field="option",
        queryset=AttributeOption.objects.get_queryset(),
    )

    def create(self, validated_data):
        existing_option = find_existing_attribute_option_group(
            validated_data["name"], validated_data["options"]
        )
        if existing_option is not None:
            return existing_option
        else:
            options = validated_data.pop("options", None)
            instance = super(AttributeOptionGroupSerializer, self).create(
                validated_data
            )
            options = bound_unique_together_get_or_create_multiple(
                instance.options, options
            )
            instance.options.set(options)
            return instance

    def update(self, instance, validated_data):
        existing_option = find_existing_attribute_option_group(
            validated_data["name"], validated_data["options"]
        )
        if existing_option is not None:
            return existing_option
        else:
            options = validated_data.pop("options", None)
            updated_instance = super(AttributeOptionGroupSerializer, self).update(
                instance, validated_data
            )
            # if the field was returned unbound,
            options = bound_unique_together_get_or_create_multiple(
                updated_instance.options, options
            )
            updated_instance.options.set(options, bulk=False)
            if not self.partial:
                # we need to manually remove the options
                updated_instance.options.exclude(
                    pk__in=[o.pk for o in options]
                ).delete()

            return updated_instance

    class Meta:
        model = AttributeOptionGroup
        fields = "__all__"


class BaseCategorySerializer(OscarHyperlinkedModelSerializer):
    breadcrumbs = serializers.CharField(source="full_name", read_only=True)

    class Meta:
        model = Category
        exclude = ("path", "depth", "numchild")


class CategorySerializer(BaseCategorySerializer):
    children = serializers.HyperlinkedIdentityField(
        view_name="category-child-list",
        lookup_field="full_slug",
        lookup_url_kwarg="breadcrumbs",
    )


class ProductAttributeListSerializer(UpdateListSerializer):
    def select_existing_item(self, manager, datum):
        try:
            return manager.get(product_class=datum["product_class"], code=datum["code"])
        except manager.model.DoesNotExist:
            pass
        except manager.model.MultipleObjectsReturned as e:
            logger.error("Multiple objects on unique contrained items, freaky %s", e)
            logger.exception(e)

        return None


class ProductAttributeSerializer(OscarHyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="admin-productattribute-detail"
    )
    product_class = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=ProductClass.objects.get_queryset(),
        write_only=True,
        required=False,
    )
    option_group = AttributeOptionGroupSerializer(required=False, allow_null=True)

    def create(self, validated_data):
        option_group = validated_data.pop("option_group", None)
        instance = super(ProductAttributeSerializer, self).create(validated_data)
        return self.update(instance, {"option_group": option_group})

    def update(self, instance, validated_data):
        option_group = validated_data.pop("option_group", None)
        updated_instance = super(ProductAttributeSerializer, self).update(
            instance, validated_data
        )
        if option_group is not None:
            serializer = self.fields["option_group"]
            # use the serializer to update the attribute_values
            if instance.option_group:
                updated_instance.option_group = serializer.update(
                    instance.option_group, option_group
                )
            else:
                updated_instance.option_group = serializer.create(option_group)

            updated_instance.save()

        return updated_instance

    class Meta:
        model = ProductAttribute
        list_serializer_class = ProductAttributeListSerializer
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
        fields = settings.OPTION_FIELDS
        list_serializer_class = UpdateForwardManyToManySerializer


class ProductAttributeValueListSerializer(UpdateListSerializer):
    # pylint: disable=unused-argument
    def shortcut_to_internal_value(self, data, productclass, attributes):
        difficult_attributes = {
            at.code: at
            for at in productclass.attributes.filter(
                type__in=[
                    ProductAttribute.OPTION,
                    ProductAttribute.MULTI_OPTION,
                    ProductAttribute.DATE,
                    ProductAttribute.DATETIME,
                    ProductAttribute.ENTITY,
                    ProductAttribute.FILE,
                    ProductAttribute.IMAGE,
                ]
            )
        }
        cv = AttributeConverter(self.context)
        internal_value = []
        for item in data:
            code, value = getitems(item, "code", "value")
            if code is None:  # delegate error state to child serializer
                internal_value.append(self.child.to_internal_value(item))

            if code in difficult_attributes:
                attribute = difficult_attributes[code]
                converted_value = cv.to_attribute_type_value(attribute, code, value)
                internal_value.append(
                    {
                        "value": converted_value,
                        "attribute": attribute,
                        "product_class": productclass,
                    }
                )
            else:
                internal_value.append(
                    {
                        "value": value,
                        "attribute": code,
                        "product_class": productclass,
                    }
                )

        return internal_value

    def to_internal_value(self, data):
        productclasses = set()
        attributes = set()
        parent = None

        for item in data:
            product_class, code = getitems(item, "product_class", "code")
            if product_class:
                productclasses.add(product_class)
            if "parent" in item and item["parent"] is not None:
                parent = item["parent"]
            attributes.add(code)

        # if all attributes belong to the same productclass, everything is just
        # as expected and we can take a shortcut by only resolving the
        # productclass to the model instance and nothing else.
        attrs_valid = all(attributes)  # no missing attribute codes?
        if attrs_valid:
            try:
                if len(productclasses):
                    (product_class,) = productclasses
                    pc = ProductClass.objects.get(slug=product_class)
                    return self.shortcut_to_internal_value(data, pc, attributes)
                elif parent:
                    pc = ProductClass.objects.get(products__id=parent)
                    return self.shortcut_to_internal_value(data, pc, attributes)
            except ProductClass.DoesNotExist:
                pass

        # if we get here we can't take the shortcut, just let everything be
        # processed by the original serializer and handle the errors.
        return super().to_internal_value(data)

    def get_value(self, dictionary):
        values = super(ProductAttributeValueListSerializer, self).get_value(dictionary)
        if values is empty:
            return values

        product_class, parent = getitems(dictionary, "product_class", "parent")
        return [
            dict(value, product_class=product_class, parent=parent) for value in values
        ]

    def to_representation(self, data):
        if isinstance(data, Manager):
            # use a cached query from product.attr to get the attributes instead
            # if an silly .all() that clones the queryset and performs a new query
            _, product = self.get_name_and_rel_instance(data)
            iterable = product.attr.get_values()
        else:
            iterable = data

        return [self.child.to_representation(item) for item in iterable]

    def update(self, instance, validated_data):
        assert isinstance(instance, Manager)

        _, product = self.get_name_and_rel_instance(instance)

        attr_codes = []
        product.attr.initialize()
        for validated_datum in validated_data:
            # leave all the attribute saving to the ProductAttributesContainer instead
            # of the child serializers
            attribute, value = getitems(validated_datum, "attribute", "value")
            if hasattr(
                attribute, "code"
            ):  # if the attribute is a model instance use the code
                product.attr.set(attribute.code, value, validate_identifier=False)
                attr_codes.append(attribute.code)
            else:
                product.attr.set(attribute, value, validate_identifier=False)
                attr_codes.append(attribute)

        # if we don't clear the dirty attributes all parent attributes
        # are marked as explicitly set, so they will be copied to the
        # child product.
        product.attr._dirty.clear()  # pylint: disable=protected-access
        product.attr.save()
        # we have to make sure to use the correct db_manager in a multidatabase
        # context, we make sure to use the same database as the passed in manager
        local_attribute_values = product.attribute_values.db_manager(
            instance.db
        ).filter(attribute__code__in=attr_codes)
        return list(local_attribute_values)


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
        Since there is a unique constraint, sometimes we want to update instead
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
        fields = settings.PRODUCT_ATTRIBUTE_VALUE_FIELDS


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
        fields = settings.RECOMMENDED_PRODUCT_FIELDS


class ProductStockRecordSerializer(OscarModelSerializer):
    url = DrillDownHyperlinkedIdentityField(
        view_name="product-stockrecord-detail",
        extra_url_kwargs={"product_pk": "product_id"},
    )

    class Meta:
        model = StockRecord
        fields = "__all__"


class BaseProductSerializer(OscarModelSerializer):
    "Base class shared by admin and public serializer"
    attributes = ProductAttributeValueSerializer(
        many=True, required=False, source="attribute_values"
    )
    categories = CategoryField(many=True, required=False)
    product_class = serializers.SlugRelatedField(
        slug_field="slug", queryset=ProductClass.objects, allow_null=True
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

    def validate(self, attrs):
        if "structure" in attrs and "parent" in attrs:
            if attrs["structure"] == Product.CHILD and attrs["parent"] is None:
                raise serializers.ValidationError(_("child without parent"))
        if "structure" in attrs and "product_class" in attrs:
            if attrs["product_class"] is None and attrs["structure"] != Product.CHILD:
                raise serializers.ValidationError(
                    _("product_class can not be empty for structure %(structure)s")
                    % attrs
                )

        return super(BaseProductSerializer, self).validate(attrs)

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


class ChildProductSerializer(PublicProductSerializer):
    "Serializer for child products"
    parent = serializers.HyperlinkedRelatedField(
        view_name="product-detail",
        queryset=Product.objects.filter(structure=Product.PARENT),
    )
    # the below fields can be filled from the parent product if enabled.
    images = ProductImageSerializer(many=True, required=False, source="parent.images")
    description = serializers.CharField(source="parent.description")

    class Meta(PublicProductSerializer.Meta):
        fields = settings.CHILDPRODUCTDETAIL_FIELDS


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
    children = ChildProductSerializer(many=True, required=False)

    stockrecords = serializers.HyperlinkedIdentityField(
        view_name="product-stockrecords", read_only=True
    )

    class Meta(PublicProductSerializer.Meta):
        fields = settings.PRODUCTDETAIL_FIELDS


class ProductLinkSerializer(ProductSerializer):
    """
    Summary serializer for list view, listing all products.

    This serializer can be easily made to show any field on ``ProductSerializer``,
    just add fields to the ``OSCARAPI_PRODUCT_FIELDS`` setting.
    """

    class Meta(PublicProductSerializer.Meta):
        fields = settings.PRODUCT_FIELDS


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
