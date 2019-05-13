from rest_framework import serializers
from oscar.core.loading import get_model

from oscarapi.utils.loading import get_api_classes, get_api_class
from oscarapi.utils.models import fake_autocreated

Product = get_model("catalogue", "Product")
StockRecordSerializer = get_api_class("serializers.basket", "StockRecordSerializer")
BaseProductSerializer, ProductImageSerializer = get_api_classes(
    "serializers.product", [
        "BaseProductSerializer", "ProductImageSerializer"
    ]
)


class AdminProductSerializer(BaseProductSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='admin-product-detail')
    stockrecords = StockRecordSerializer(many=True, required=False)
    images = ProductImageSerializer(many=True, required=False)
    children = serializers.HyperlinkedRelatedField(
        view_name="admin-product-detail",
        many=True,
        required=False,
        queryset=Product.objects.filter(structure=Product.CHILD)
    )

    class Meta(BaseProductSerializer.Meta):
        exclude = ("product_options", )

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

        instance.attribute_values.set(attribute_values)
        instance.images.set(images)

        return super(AdminProductSerializer, self).update(instance, validated_data)
