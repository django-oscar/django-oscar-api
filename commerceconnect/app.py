from oscar.core.application import Application
from oscar.views.decorators import permissions_required

from commerceconnect.urls import urlpatterns


class CommerceConnectApplication(Application):
    def get_url_decorator(self, pattern):
        "Fixes bug in Application.get_url_decorator wich would decorate None values."
        permissions = self.get_permissions(pattern.name)
        if permissions is not None:
            return permissions_required(permissions)

        return None

    def get_urls(self):
        return self.post_process_urls(urlpatterns)


application = CommerceConnectApplication()
