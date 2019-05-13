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

    def update(self, instance, validated_data):
        "Handle the nested serializers manually"
        attribute_values = validated_data.pop("attribute_values", [])
        options = validated_data.pop("options", [])
        stockrecords = validated_data.pop("stockrecords", [])
        images = validated_data.pop("images", [])
        categories = validated_data.pop("categories", [])
        recommended_products = validated_data.pop("recommended_products", [])

        # remove the very annoying "Cannot set values on a ManyToManyField which
        # specifies an intermediary model" error, which does not apply at all
        # to these models because they have sane defaults.
        with fake_autocreated(instance.categories) as _categories:
            _categories.set(categories)
        with fake_autocreated(instance.recommended_products) as _recommended_products:
            _recommended_products.set(recommended_products)
        with fake_autocreated(instance.product_options) as _product_options:
            pclass_options = instance.get_product_class().options.all()
            _product_options.set(set(options) - set(pclass_options))

        instance.images.set(images)
        instance.stockrecords.set(stockrecords)

        # update instance
        instance = super(AdminProductSerializer, self).update(instance, validated_data)

        # deal with attributes after saving instance
        # get the serializer
        attribute_serializer = self.fields["attributes"]

        # use the serializer to update the attribute_values
        updated_attribute_values = attribute_serializer.update(
            instance.attribute_values, attribute_values
        )
        # add the updated_attribute_values to the instance
        instance.attribute_values.add(*updated_attribute_values)
        # remove all the obsolete attribute values, this could be caused by
        # the product class changing for example, lots of attributes would become
        # obsolete.
        current_pks = [p.pk for p in updated_attribute_values]
        instance.attribute_values.exclude(pk__in=current_pks).delete()

        return instance
