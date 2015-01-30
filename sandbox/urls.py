from django.conf.urls import patterns, include, url
from django.contrib import admin
from oscar.app import application
from oscarapi.app import application as api

urlpatterns = patterns('',
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include(api.urls)),
    url(r'', include(application.urls)),
)
