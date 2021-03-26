from django.db import transaction
from django.template.defaultfilters import slugify

from rest_framework import serializers
from rest_framework.exceptions import APIException

from oscar.core.loading import get_model

from oscarapi.serializers.utils import OscarHyperlinkedModelSerializer
from oscarapi.utils.categories import create_from_full_slug
from oscarapi.utils.loading import get_api_classes, get_api_class
from oscarapi.utils.models import fake_autocreated

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
Option = get_model("catalogue", "Option")
AdminStockRecordSerializer = get_api_class(
    "serializers.admin.partner", "AdminStockRecordSerializer"
)
(
    BaseProductSerializer,
    BaseCategorySerializer,
    ProductImageSerializer,
    ProductAttributeSerializer,
    OptionSerializer,
) = get_api_classes(
    "serializers.product",
    [
        "BaseProductSerializer",
        "BaseCategorySerializer",
        "ProductImageSerializer",
        "ProductAttributeSerializer",
        "OptionSerializer",
    ],
)


class AdminProductSerializer(BaseProductSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="admin-product-detail")
    stockrecords = AdminStockRecordSerializer(many=True, required=False)
    images = ProductImageSerializer(many=True, required=False)
    children = serializers.HyperlinkedRelatedField(
        view_name="admin-product-detail",
        many=True,
        required=False,
        queryset=Product.objects.filter(structure=Product.CHILD),
    )

    class Meta(BaseProductSerializer.Meta):
        exclude = ("product_options",)

    def create(self, validated_data):
        attribute_values = validated_data.pop("attribute_values", None)
        options = validated_data.pop("options", None)
        stockrecords = validated_data.pop("stockrecords", None)
        images = validated_data.pop("images", None)
        categories = validated_data.pop("categories", None)
        recommended_products = validated_data.pop("recommended_products", None)
        children = validated_data.pop("children", None)

        with transaction.atomic():  # it is all or nothing!

            # update instance
            self.instance = (  # pylint:disable=attribute-defined-outside-init
                instance
            ) = super(AdminProductSerializer, self).create(validated_data)
            return self.update(
                instance,
                dict(
                    validated_data,
                    attribute_values=attribute_values,
                    options=options,
                    stockrecords=stockrecords,
                    images=images,
                    categories=categories,
                    recommended_products=recommended_products,
                    children=children,
                ),
            )

    def update(self, instance, validated_data):
        "Handle the nested serializers manually"
        attribute_values = validated_data.pop("attribute_values", None)
        options = validated_data.pop("options", None)
        stockrecords = validated_data.pop("stockrecords", None)
        images = validated_data.pop("images", None)
        categories = validated_data.pop("categories", None)
        recommended_products = validated_data.pop("recommended_products", None)
        children = validated_data.pop("children", None)

        with transaction.atomic():  # it is all or nothing!

            # update instance
            instance = super(AdminProductSerializer, self).update(
                instance, validated_data
            )

            # ``fake_autocreated`` removes the very annoying "Cannot set values
            # on a ManyToManyField which specifies an intermediary model" error,
            # which does not apply at all to these models because they have sane
            # defaults.

            if categories is not None:
                with fake_autocreated(instance.categories) as _categories:
                    if self.partial:
                        _categories.add(*categories)
                    else:
                        _categories.set(categories)

            if recommended_products is not None:
                with fake_autocreated(
                    instance.recommended_products
                ) as _recommended_products:
                    if self.partial:
                        _recommended_products.add(*recommended_products)
                    else:
                        _recommended_products.set(recommended_products)

            if children is not None:
                if self.partial:
                    instance.children.add(*children)
                else:
                    instance.children.set(children)

            product_class = instance.get_product_class()
            pclass_option_codes = set()
            if options is not None:
                with fake_autocreated(instance.product_options) as _product_options:
                    pclass_option_codes = product_class.options.filter(
                        code__in=[opt["code"] for opt in options]
                    ).values_list("code", flat=True)
                    # only options not allready defined on the product class are important
                    new_options = [
                        opt for opt in options if opt["code"] not in pclass_option_codes
                    ]
                    self.update_relation("options", _product_options, new_options)

            self.update_relation("images", instance.images, images)
            self.update_relation("stockrecords", instance.stockrecords, stockrecords)
            self.update_relation(
                "attributes", instance.attribute_values, attribute_values
            )

            if (
                self.partial
            ):  # we need to clean up all the attributes with wrong product class
                for attribute_value in instance.attribute_values.exclude(
                    attribute__product_class=product_class
                ):
                    code = attribute_value.attribute.code
                    if (
                        code in pclass_option_codes
                    ):  # if the attribute exist also on the new product class, update the attribute
                        attribute_value.attribute = product_class.attributes.get(
                            code=code
                        )
                        attribute_value.save()
                    else:
                        attribute_value.delete()
            # return a refreshed instance so we are sure all attributes are reloaded
            # from the database again when accessed. An attr.refresh() method
            # was added in Oscar 3, but that will not delete any existsing
            # attributes which  have become invalid (after updating the
            # product class for example)
            return instance._meta.model.objects.get(pk=instance.pk)


class AdminCategorySerializer(BaseCategorySerializer):
    url = serializers.HyperlinkedIdentityField(view_name="admin-category-detail")
    children = serializers.HyperlinkedIdentityField(
        view_name="admin-category-child-list",
        lookup_field="full_slug",
        lookup_url_kwarg="breadcrumbs",
    )
    slug = serializers.SlugField(required=False)

    def create(self, validated_data):
        breadcrumbs = self.context.get("breadcrumbs", None)
        slug = validated_data.get("slug", slugify(validated_data["name"]))

        if breadcrumbs is None:
            breadcrumbs = slug
        else:
            breadcrumbs = "/".join((breadcrumbs, slug))

        try:
            instance = create_from_full_slug(breadcrumbs, separator="/")
        except ValueError as e:
            raise APIException(str(e))

        return self.update(instance, validated_data)


class AdminProductClassSerializer(OscarHyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="admin-productclass-detail", lookup_field="slug"
    )
    attributes = ProductAttributeSerializer(many=True, required=False)
    options = OptionSerializer(many=True, required=False)

    def create(self, validated_data):
        attributes = validated_data.pop("attributes", None)
        options = validated_data.pop("options", None)

        with transaction.atomic():
            self.instance = instance = super(AdminProductClassSerializer, self).create(
                validated_data
            )
            return self.update(
                instance, dict(validated_data, attributes=attributes, options=options)
            )

    def update(self, instance, validated_data):
        attributes = validated_data.pop("attributes", None)
        options = validated_data.pop("options", None)

        with transaction.atomic():
            updated_instance = super(AdminProductClassSerializer, self).update(
                instance, validated_data
            )
            self.update_relation("attributes", updated_instance.attributes, attributes)
            self.update_relation("options", instance.options, options)

            return updated_instance

    class Meta:
        model = ProductClass
        fields = "__all__"
