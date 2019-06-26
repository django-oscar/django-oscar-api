from six.moves import reload_module

from django.urls import reverse

from oscarapi.tests.utils import APITest

from oscarapi import urls


class BlockAdminApiTest(APITest):
    def test_root_view(self):
        "The admin api views should not be in the root view when OSCARAPI_BLOCK_ADMIN_API_ACCESS is True"
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            self.response = self.get(reverse("api-root"))
            self.response.assertStatusEqual(200)
            # so the admin api is not shown in the root view as we are not logged in as staff user
            self.assertNotIn("admin", self.response.data)

            # now we are
            self.login('admin', 'admin')
            self.response = self.get(reverse("api-root"))
            self.response.assertStatusEqual(200)
            self.assertIn("admin", self.response.data)

        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=True):
            self.response = self.get(reverse("api-root"))
            self.response.assertStatusEqual(200)
            # so the admin api is not shown in the root view
            self.assertNotIn("admin", self.response.data)

            # even when we are logged in as admin
            self.login('admin', 'admin')
            self.response = self.get(reverse("api-root"))
            self.response.assertStatusEqual(200)
            self.assertNotIn("admin", self.response.data)

    def test_urlconf(self):
        "The admin api urls should not be registered when OSCARAPI_BLOCK_ADMIN_API_ACCESS is True"
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            urlpattern_names = [url.name for url in urls.urlpatterns]

            for pattern in urls.admin_urlpatterns:
                self.assertIn(pattern.name, urlpattern_names)

        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=True):
            reload_module(urls)
            urlpattern_names = [url.name for url in urls.urlpatterns]

            for pattern in urls.admin_urlpatterns:
                self.assertNotIn(pattern.name, urlpattern_names)
