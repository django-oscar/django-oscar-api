from oscar.core.loading import get_class

from rest_framework import serializers
from oscarapi.serializers import checkout, product


Selector = get_class("partner.strategy", "Selector")


class ProductLinkSerializer(product.ProductLinkSerializer):
    price = serializers.SerializerMethodField()

    class Meta(product.ProductLinkSerializer.Meta):
        fields = ('url', 'id', 'title', 'images', 'price')

    def get_price(self, instance):
        request = self.context.get("request")
        strategy = Selector().strategy(request=request, user=request.user)

        ser = checkout.PriceSerializer(
            strategy.fetch_for_product(instance).price,
            context={'request': request})

        return ser.data
