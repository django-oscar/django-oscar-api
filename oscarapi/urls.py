from django.urls import path, re_path

from rest_framework.urlpatterns import format_suffix_patterns

from oscarapi import views

urlpatterns = [
    path('', views.api_root, name='api-root'),
    path('login/', views.LoginView.as_view(), name='api-login'),
    path('basket/', views.BasketView.as_view(), name='api-basket'),
    path('basket/add-product/', views.AddProductView.as_view(), name='api-basket-add-product'),
    path('basket/add-voucher/', views.AddVoucherView.as_view(), name='api-basket-add-voucher'),
    path('basket/shipping-methods/', views.ShippingMethodView.as_view(), name='api-basket-shipping-methods'),
    path('baskets/', views.BasketList.as_view(), name='basket-list'),
    path('baskets/<int:pk>/', views.BasketDetail.as_view(), name='basket-detail'),
    path('baskets/<int:pk>/lines/', views.LineList.as_view(), name='basket-lines-list'),
    path('baskets/<int:basket_pk>/lines/<int:pk>/', views.BasketLineDetail.as_view(), name='basket-line-detail'),
    path('lines/', views.LineList.as_view(), name='line-list'),
    path('lines/<int:pk>/', views.LineDetail.as_view(), name='line-detail'),
    path('lineattributes/', views.LineAttributeList.as_view(), name='lineattribute-list'),
    path('lineattributes/<int:pk>/', views.LineAttributeDetail.as_view(), name='lineattribute-detail'),
    path('products/', views.ProductList.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetail.as_view(), name='product-detail'),
    path('products/<int:pk>/price/', views.ProductPrice.as_view(), name='product-price'),
    path('products/<int:pk>/availability/', views.ProductAvailability.as_view(), name='product-availability'),
    path('products/<int:pk>/stockrecords/', views.StockRecordList.as_view(), name='product-stockrecord-list'),
    path('stockrecords/', views.StockRecordList.as_view(), name='stockrecord-list'),
    path('stockrecords/<int:pk>/', views.StockRecordDetail.as_view(), name='stockrecord-detail'),
    path('options/', views.OptionList.as_view(), name='option-list'),
    path('options/<int:pk>/', views.OptionDetail.as_view(), name='option-detail'),
    path('users/', views.UserList.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
    path('checkout/', views.CheckoutView.as_view(), name='api-checkout'),
    path('orders/', views.OrderList.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.OrderDetail.as_view(), name='order-detail'),
    path('orders/<int:pk>/lines/', views.OrderLineList.as_view(), name='order-lines-list'),
    path('orderlines/<int:pk>/', views.OrderLineDetail.as_view(), name='order-lines-detail'),
    path('orderlineattributes/<int:pk>/', views.OrderLineAttributeDetail.as_view(), name='order-lineattributes-detail'),
    path('countries/', views.CountryList.as_view(), name='country-list'),
    re_path(r'^countries/(?P<pk>[A-z]{2})/$', views.CountryDetail.as_view(), name='country-detail'),
    path('partners/', views.PartnerList.as_view(), name='partner-list'),
    path('partners/<int:pk>/', views.PartnerDetail.as_view(), name='partner-detail'),
    path('useraddresses/', views.UserAddressList.as_view(), name='useraddress-list'),
    path('useraddresses/<int:pk>/', views.UserAddressDetail.as_view(), name='useraddress-detail')
]

urlpatterns = format_suffix_patterns(urlpatterns)
