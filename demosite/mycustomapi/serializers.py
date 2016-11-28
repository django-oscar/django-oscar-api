from oscarapi.serializers.product import (
    ProductImageSerializer, ProductLinkSerializer)


class MyProductLinkSerializer(ProductLinkSerializer):
    images = ProductImageSerializer(many=True, required=False)

    class Meta(ProductLinkSerializer.Meta):
        fields = ('url', 'id', 'title', 'images')
