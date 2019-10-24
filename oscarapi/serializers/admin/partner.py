from rest_framework import serializers

from oscar.core.loading import get_model
from oscarapi.serializers.utils import (
    DelayUniqueSerializerMixin,
    OscarHyperlinkedModelSerializer,
    UpdateListSerializer,
)

Product = get_model("catalogue", "Product")
StockRecord = get_model("partner", "StockRecord")


class AdminStockRecordSerializer(
    DelayUniqueSerializerMixin, OscarHyperlinkedModelSerializer
):
    url = serializers.HyperlinkedIdentityField(view_name="admin-stockrecord-detail")

    product = serializers.PrimaryKeyRelatedField(
        many=False, required=False, queryset=Product.objects
    )

    class Meta:
        model = StockRecord
        fields = "__all__"
        list_serializer_class = UpdateListSerializer
