from django.urls import path
from django.contrib import admin

from oscar.app import application as oscar
from oscarapi.app import application as api


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('', oscar.urls),
]
