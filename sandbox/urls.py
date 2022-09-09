from django.apps import apps
from django.urls import include, path
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
    path('api/', include('oscarapi.urls')),
    path('js-login-example/', TemplateView.as_view(template_name='js-login-example.html')),
    path('', include(apps.get_app_config('oscar').urls[0]))
]
