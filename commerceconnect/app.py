from commerceconnect.urls import urlpatterns
from oscar.core.application import Application


class CommerceConnectApplication(Application):
    name = 'commerceconnect'

    def get_urls(self):
        
        return self.post_process_urls(urlpatterns)


application = CommerceConnectApplication()
