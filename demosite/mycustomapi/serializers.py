from oscarapi.serializers.product import (
    ProductImageSerializer, ProductLinkSerializer)


class MyProductListSerializer(ProductLinkSerializer):
    images = ProductImageSerializer(many=True, required=False)

    class Meta(ProductLinkSerializer.Meta):
        fields = ('url', 'id', 'title', 'images')
