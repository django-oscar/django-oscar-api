from django.conf.urls import url

from mycustomapi import views

from oscarapi.app import RESTApiApplication


class MyRESTApiApplication(RESTApiApplication):

    def get_urls(self):
        urls = [url(
            r'^products/$',
            views.ProductList.as_view(), name='product-list')]

        return urls + super(MyRESTApiApplication, self).get_urls()

application = MyRESTApiApplication()
