import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse

from oscarapi import urls
from oscarapi.tests.utils import APITest

from oscarapi.permissions import APIAdminPermission

User = get_user_model()


class BlockAdminApiTest(APITest):
    def test_root_view(self):
        "The admin api views should not be in the root view when OSCARAPI_BLOCK_ADMIN_API_ACCESS is True"
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            self.reload_modules([urls, sys.modules[settings.ROOT_URLCONF]])
            self.response = self.get(reverse("api-root"))
            self.response.assertStatusEqual(200)
            # so the admin api is not shown in the root view as we are not logged in as staff user
            self.assertNotIn("admin", self.response.data)

            # now we are
            self.login("admin", "admin")
            self.response = self.get(reverse("api-root"))
            self.response.assertStatusEqual(200)
            self.assertIn("admin", self.response.data)

        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=True):
            self.reload_modules([urls, sys.modules[settings.ROOT_URLCONF]])
            self.response = self.get(reverse("api-root"))
            self.response.assertStatusEqual(200)
            # so the admin api is not shown in the root view
            self.assertNotIn("admin", self.response.data)

            # even when we are logged in as admin
            self.login("admin", "admin")
            self.response = self.get(reverse("api-root"))
            self.response.assertStatusEqual(200)
            self.assertNotIn("admin", self.response.data)

    def test_urlconf(self):
        "The admin api urls should not be registered when OSCARAPI_BLOCK_ADMIN_API_ACCESS is True"
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            self.reload_modules([urls, sys.modules[settings.ROOT_URLCONF]])
            urlpattern_names = [url.name for url in urls.urlpatterns]

            for pattern in urls.admin_urlpatterns:
                self.assertIn(pattern.name, urlpattern_names)

        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=True):
            self.reload_modules([urls, sys.modules[settings.ROOT_URLCONF]])
            urlpattern_names = [url.name for url in urls.urlpatterns]

            for pattern in urls.admin_urlpatterns:
                self.assertNotIn(pattern.name, urlpattern_names)

    def test_api_admin_permission(self):
        permission = APIAdminPermission()
        request = RequestFactory()

        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            # nobody can't access the admin api
            request.user = User.objects.get(username="nobody")
            self.assertTrue(
                permission.disallowed_by_setting_and_request(request),
                "a non staff user can't access the admin api",
            )

            # but a staff user can
            request.user = User.objects.get(username="admin")
            self.assertFalse(
                permission.disallowed_by_setting_and_request(request),
                "a staff user can access the admin api",
            )

        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=True):
            # nobody can't access the admin api
            request.user = User.objects.get(username="nobody")
            self.assertTrue(
                permission.disallowed_by_setting_and_request(request),
                "a non staff user can't access the admin api",
            )

            # and a staff user can't access it either when
            # OSCARAPI_BLOCK_ADMIN_API_ACCESS=True
            request.user = User.objects.get(username="admin")
            self.assertTrue(
                permission.disallowed_by_setting_and_request(request),
                "a staff user can't access the admin api with "
                "OSCARAPI_BLOCK_ADMIN_API_ACCESS=True",
            )
