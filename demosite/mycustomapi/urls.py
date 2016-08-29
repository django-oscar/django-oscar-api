"""demosite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin

from mycustomapi import views

from oscar.app import application as oscar
from oscarapi.app import application as api


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # we override the product-list to show the override of a serializer
    url(r'^api/products/$', views.ProductList.as_view(), name='product-list'),

    url(r'^api/', include(api.urls)),
    url(r'', include(oscar.urls)),

]
