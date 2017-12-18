from rest_framework import serializers

from oscar.core.loading import get_class

from oscarapi.serializers.checkout import PriceSerializer
from oscarapi.serializers.product import (
    ProductImageSerializer, ProductLinkSerializer
)


Selector = get_class('partner.strategy', 'Selector')


class MyProductLinkSerializer(ProductLinkSerializer):
    images = ProductImageSerializer(many=True, required=False)
    price = serializers.SerializerMethodField()

    class Meta(ProductLinkSerializer.Meta):
        fields = ('url', 'id', 'title', 'images', 'price')

    def get_price(self, obj):
        request = self.context.get("request")
        strategy = Selector().strategy(
            request=request, user=request.user)
        ser = PriceSerializer(
            strategy.fetch_for_product(obj).price,
            context={'request': request})
        return ser.data
