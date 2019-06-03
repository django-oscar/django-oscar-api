from rest_framework import serializers
from oscarapi.serializers import checkout


class CountrySerializer(checkout.CountrySerializer):
    is_benelux_country = serializers.SerializerMethodField()

    def get_is_benelux_country(self, obj):
        return obj.iso_3166_1_a2.lower() in ("nl", "be", "lu")
