from django.conf.urls import url
from django.contrib import admin

from oscar.app import application as oscar
from oscarapi.app import application as api


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', api.urls),
    url(r'', oscar.urls),
]
