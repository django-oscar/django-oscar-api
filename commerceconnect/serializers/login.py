from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

from commerceconnect.utils import overridable


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = overridable('CC_USER_FIELDS', ('username', 'id', 'date_joined',))


class LoginSerializer(serializers.Serializer):

    username = serializers.CharField(max_length=30, required=True)
    password = serializers.CharField(max_length=255, required=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'],
                                       password=attrs['password'])
        if user is None:
            raise serializers.ValidationError('invalid login')
        elif not user.is_active:
            raise serializers.ValidationError('Can not log in as inactive user')
        elif user.is_staff and overridable('CC_BLOCK_ADMIN_API_ACCESS', True):
            raise serializers.ValidationError('Staff users can not log in via the rest api')

        return attrs

    def restore_object(self, attrs, instance=None):
        return authenticate(username=attrs['username'],
                                       password=attrs['password'])
