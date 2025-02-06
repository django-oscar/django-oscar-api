from django.apps import apps
from django.urls import include, path, re_path
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
    path('api/', include('oscarapi.urls')),
    path('razorpay/', include('django_oscar_api_razorpay.urls')),
    re_path(r'^pay/razorpay/', include('django_oscar_razorpay.urls')),
    path('js-login-example/', TemplateView.as_view(template_name='js-login-example.html')),
    path('', include(apps.get_app_config('oscar').urls[0]))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
