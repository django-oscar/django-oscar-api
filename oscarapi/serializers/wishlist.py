from rest_framework import serializers
from oscar.core.loading import get_model
from oscarapi.serializers.product import ProductSerializer

WishList = get_model("wishlists", "WishList")
Line = get_model("wishlists", "Line")

class LineSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True,fields=("id", "options","stockrecords","images","services","title", "url","selling_price","original_price","price_currency"))  # Nested serializer for the product field

    class Meta:
        model = Line
        fields = ["id", "product", "quantity", "title"]
        read_only_fields = ["wishlist", "title"]  

class WishListSerializer(serializers.ModelSerializer):
    lines = LineSerializer(many=True, read_only=True)  

    class Meta:
        model = WishList
        fields = ["id", "name", "visibility", "date_created","key", "lines"]