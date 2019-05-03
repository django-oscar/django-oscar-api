from django.apps import apps
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(apps.get_app_config('oscarapi').urls[0])),
    url(r'', include(apps.get_app_config('oscar').urls[0]))
]
