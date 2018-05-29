from django.conf.urls import url

from oscarapi.app import RESTApiApplication

from . import views


class MyRESTApiApplication(RESTApiApplication):

    def get_urls(self):
        urls = [url(
            r'^products/$',
            views.ProductList.as_view(), name='product-list')]

        return urls + super(MyRESTApiApplication, self).get_urls()


application = MyRESTApiApplication()
