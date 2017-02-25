from django.conf.urls import include, url
from django.contrib import admin
from oscar.app import application
from oscarapi.app import application as api

urlpatterns = [
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include(api.urls)),
    url(r'', include(application.urls)),
]
