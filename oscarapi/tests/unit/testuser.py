from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from oscarapi.tests.utils import APITest


User = get_user_model()


class UserTest(APITest):
    """
    Check the users are properly created bys setUp.

    Let's do it this way instead of fixtures, because it is pretty likely
    that the User model has been changed by other people, which means the
    fixtures might not fit.
    """

    def test_admin_user(self):
        "Admin user can authenticate with django via the html frontend"
        self.login("admin", "admin")
        self.assertEqual(int(self.client.session["_auth_user_id"]), 1)

    def test_non_admin_user(self):
        "Regular user can authenticate with django via the html frontend"
        self.login("nobody", "nobody")
        self.assertEqual(int(self.client.session["_auth_user_id"]), 2)

    def test_admin_header(self):
        self.hlogin("admin", "admin", "admin")

    def test_non_admin_header(self):
        self.hlogin("nobody", "nobody", "nobody")


class UserDetailTest(APITest):
    """
    Check if we can access our own user details when authenticated and when
    OSCARAPI_EXPOSE_USER_DETAILS is set to True
    """

    def test_expose_user_detail_allowed(self):
        "The user nobody can retrieve it's own user details"
        self.login("nobody", "nobody")
        user = User.objects.get(username="nobody")
        url = reverse("user-detail", args=(user.id,))

        self.response = self.get(url)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("username", user.username)

    def test_expose_user_detail_from_other_users_not_found(self):
        "The user nobody cannot retrieve other users details"
        self.login("nobody", "nobody")
        url = reverse("user-detail", args=(1,))

        self.response = self.get(url)
        self.response.assertStatusEqual(404)

    @override_settings(OSCARAPI_EXPOSE_USER_DETAILS=False)
    def test_expose_user_detail_not_allowed(self):
        "The user nobody can not retrieve it's own user details (disabled)"
        self.login("nobody", "nobody")
        user = User.objects.get(username="nobody")
        url = reverse("user-detail", args=(user.id,))

        self.response = self.get(url)
        self.response.assertStatusEqual(204)
        self.assertIsNone(self.response.data)
