from django.db import transaction

from rest_framework import serializers

from oscar.core.loading import get_model

from oscarapi.utils.loading import get_api_classes, get_api_class
from oscarapi.utils.models import fake_autocreated

Product = get_model("catalogue", "Product")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
StockRecordSerializer = get_api_class("serializers.basket", "StockRecordSerializer")
BaseProductSerializer, ProductImageSerializer = get_api_classes(  # pylint: disable=unbalanced-tuple-unpacking
    "serializers.product", ["BaseProductSerializer", "ProductImageSerializer"]
)


class AdminProductSerializer(BaseProductSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="admin-product-detail")
    stockrecords = StockRecordSerializer(many=True, required=False)
    images = ProductImageSerializer(many=True, required=False)
    children = serializers.HyperlinkedRelatedField(
        view_name="admin-product-detail",
        many=True,
        required=False,
        queryset=Product.objects.filter(structure=Product.CHILD),
    )

    class Meta(BaseProductSerializer.Meta):
        exclude = ("product_options",)

    def update_relation(self, name, manager, values):
        if values is None:
            return

        serializer = self.fields[name]

        # use the serializer to update the attribute_values
        updated_values = serializer.update(manager, values)

        if self.partial:
            manager.add(*updated_values)
        elif hasattr(manager, "field") and not manager.field.null:
            # add the updated_attribute_values to the instance
            manager.add(*updated_values)
            # remove all the obsolete attribute values, this could be caused by
            # the product class changing for example, lots of attributes would become
            # obsolete.
            current_pks = [p.pk for p in updated_values]
            manager.exclude(pk__in=current_pks).delete()
        else:
            manager.set(updated_values)

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

            return instance
