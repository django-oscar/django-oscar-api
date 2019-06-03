from rest_framework import serializers
from oscarapi.serializers import login


class LoginSerializer(login.LoginSerializer):
    my_extension = serializers.SerializerMethodField()

    def get_my_extension(self, obj):
        return "I successfully managed to extend the standard oscarapi"
