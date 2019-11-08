from mock import patch
from oscarapi.tests.utils import APITest
import oscarapi.utils.loading as loading
from django.contrib.auth import get_user_model

User = get_user_model()


class ApiOverrideTest(APITest):
    def get_login_serializer(self):
        return loading.get_api_class("serializers.login", "LoginSerializer")

    def test_login_serializer_can_be_extended(self):
        user = User.objects.first()

        # get the standard serializer
        login_serializer = self.get_login_serializer()
        login_data = login_serializer(instance=user).data
        self.assertNotIn(
            "my_extension", login_data, "The serializer should not have any extension"
        )

        # now get the serializer again, but with the OSCARAPI_OVERRIDE_MODULES
        with patch.object(loading, "OSCARAPI_OVERRIDE_MODULES", ["oscarapi.tests"]):
            my_login_serializer = self.get_login_serializer()
            login_data = my_login_serializer(instance=user).data
            self.assertIn(
                "my_extension", login_data, "The serialzier should have an extension"
            )

        self.assertNotEqual(
            login_serializer,
            my_login_serializer,
            "The 2 serializers should not be the same",
        )
