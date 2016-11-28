from django.conf.urls import include, url
from django.contrib import admin

from mycustomapi.app import application as api
from oscar.app import application as oscar

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(api.urls)),
    url(r'', include(oscar.urls)),

]
