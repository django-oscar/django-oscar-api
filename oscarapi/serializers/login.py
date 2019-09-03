from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

from oscarapi.utils.settings import overridable


User = get_user_model()


def field_length(fieldname):
    field = next(field for field in User._meta.fields if field.name == fieldname)
    return field.max_length


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = overridable(
            "OSCARAPI_USER_FIELDS", default=(User.USERNAME_FIELD, "id", "date_joined")
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=field_length(User.USERNAME_FIELD), required=True
    )
    password = serializers.CharField(max_length=field_length("password"), required=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("invalid login")
        elif not user.is_active:
            raise serializers.ValidationError("Can not log in as inactive user")

        # set instance to the user so we can use this in the view
        self.instance = user
        return attrs
