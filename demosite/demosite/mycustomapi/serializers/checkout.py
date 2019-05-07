from rest_framework import serializers
from oscarapi.serializers import checkout


class CountrySerializer(checkout.CountrySerializer):
    proof_of_functionality = serializers.SerializerMethodField()

    def get_proof_of_functionality(self, obj):
        return "HELLOW WORLD"
