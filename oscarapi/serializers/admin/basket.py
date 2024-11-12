from rest_framework import serializers

from oscar.core.loading import get_model

from oscarapi.utils.loading import get_api_classes, get_api_class


Basket = get_model("basket", "Basket")
(
    BasketSerializer,
) = get_api_classes(
    "serializers.basket",
    ["BasketSerializer",]
)


class AdminBasketSerializer(BasketSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="admin-basket-detail")
