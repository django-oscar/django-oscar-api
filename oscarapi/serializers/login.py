from django.core.exceptions import ValidationError

from django.contrib.auth import get_user_model, authenticate, password_validation
from rest_framework import serializers

from oscarapi.utils.settings import overridable


User = get_user_model()


def field_length(fieldname):
    field = next(field for field in User._meta.fields if field.name == fieldname)
    return field.max_length


class UserSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = overridable(
            "OSCARAPI_USER_FIELDS",
            default=(User.USERNAME_FIELD, "email", "date_joined"),
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=field_length(User.USERNAME_FIELD), required=True
    )
    password = serializers.CharField(
        max_length=field_length("password"),
        required=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("invalid login")
        elif not user.is_active:
            raise serializers.ValidationError("Can not log in as inactive user")

        # set instance to the user so we can use this in the view
        self.instance = user
        return attrs


class RegisterUserSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=field_length("email"), required=True)
    password1 = serializers.CharField(
        max_length=field_length("password"),
        required=True,
        style={"input_type": "password"},
    )
    password2 = serializers.CharField(
        max_length=field_length("password"),
        required=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("A user with this email allready exists")

        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError("Passwords do not match")

        try:
            password_validation.validate_password(attrs["password1"])
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

        return attrs

    def create_user(self, email, password):
        # this is a separate method so it's easy to override
        return User.objects.create_user(username=email, email=email, password=password)

    def save(self):
        email = self.validated_data["email"]
        password = self.validated_data["password1"]
        return self.create_user(email, password)
