from oscar.core.application import OscarConfig


class OscarAPIConfig(OscarConfig):
    name = "oscarapi"

    def get_urls(self):
        from oscarapi.urls import urlpatterns
        return self.post_process_urls(urlpatterns)
