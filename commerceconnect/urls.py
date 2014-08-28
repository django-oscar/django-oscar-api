from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns
from commerceconnect import views


urlpatterns = patterns('',
    url(r'^$', 'commerceconnect.views.api_root', name='api-root'),
    url(r'^basket/$', views.BasketList.as_view(), name='basket-list'),
    url(r'^basket/(?P<pk>[0-9]+)/$', views.BasketDetail.as_view(), name='basket-detail'),
    url(r'^line/$', views.LineList.as_view(), name='line-list'),
    url(r'^line/(?P<pk>[0-9]+)/$', views.LineDetail.as_view(), name='line-detail'),
    url(r'^lineattribute/$', views.LineAttributeList.as_view(), name='lineattribute-list'),
    url(r'^lineattribute/(?P<pk>[0-9]+)/$', views.LineAttributeDetail.as_view(), name='lineattribute-detail'),
    url(r'^product/$', views.ProductList.as_view(), name='product-list'),
    url(r'^product/(?P<pk>[0-9]+)/$', views.ProductDetail.as_view(), name='product-detail'),
    url(r'^stockrecord/$', views.StockRecordList.as_view(), name='stockrecord-list'),
    url(r'^stockrecord/(?P<pk>[0-9]+)/$', views.StockRecordDetail.as_view(), name='stockrecord-detail'),
)

urlpatterns = format_suffix_patterns(urlpatterns)