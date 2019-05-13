from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from oscarapi.utils.loading import get_api_classes, get_api_class

api_root = get_api_class("views.root", "api_root")
LoginView = get_api_class("views.login", "LoginView")
(
    BasketView,
    AddProductView,
    AddVoucherView,
    ShippingMethodView,
    LineList,
    LineDetail,
    BasketLineDetail
) = get_api_classes(
    "views.basket", [
        "BasketView",
        "AddProductView",
        "AddVoucherView",
        "ShippingMethodView",
        "LineList",
        "LineDetail",
        "BasketLineDetail"
    ]
)

(
    BasketList,
    BasketDetail,
    LineAttributeList,
    LineAttributeDetail,
    StockRecordList,
    StockRecordDetail,
    OptionList,
    OptionDetail,
    UserList,
    UserDetail,
    CountryList,
    CountryDetail,
    PartnerList,
    PartnerDetail,
) = get_api_classes(
    "views.basic", [
        "BasketList",
        "BasketDetail",
        "LineAttributeList",
        "LineAttributeDetail",
        "StockRecordList",
        "StockRecordDetail",
        "OptionList",
        "OptionDetail",
        "UserList",
        "UserDetail",
        "CountryList",
        "CountryDetail",
        "PartnerList",
        "PartnerDetail",
    ]
)

(
    ProductList,
    ProductDetail,
    ProductPrice,
    ProductAvailability
) = get_api_classes(
    "views.product", [
        "ProductList",
        "ProductDetail",
        "ProductPrice",
        "ProductAvailability"
    ]
)

(
    CheckoutView,
    OrderList,
    OrderDetail,
    OrderLineList,
    OrderLineDetail,
    OrderLineAttributeDetail,
    UserAddressList,
    UserAddressDetail
) = get_api_classes(
    "views.checkout", [
        "CheckoutView",
        "OrderList",
        "OrderDetail",
        "OrderLineList",
        "OrderLineDetail",
        "OrderLineAttributeDetail",
        "UserAddressList",
        "UserAddressDetail"
    ]
)


urlpatterns = [
    url(r'^$', api_root, name='api-root'),
    url(r'^login/$', LoginView.as_view(), name='api-login'),
    url(r'^basket/$', BasketView.as_view(), name='api-basket'),
    url(r'^basket/add-product/$', AddProductView.as_view(), name='api-basket-add-product'),
    url(r'^basket/add-voucher/$', AddVoucherView.as_view(), name='api-basket-add-voucher'),
    url(r'^basket/shipping-methods/$', ShippingMethodView.as_view(), name='api-basket-shipping-methods'),
    url(r'^baskets/(?P<pk>[0-9]+)/$', BasketDetail.as_view(), name='basket-detail'),
    url(r'^baskets/(?P<pk>[0-9]+)/lines/$', LineList.as_view(), name='basket-lines-list'),
    url(r'^baskets/(?P<basket_pk>[0-9]+)/lines/(?P<pk>[0-9]+)/$', BasketLineDetail.as_view(), name='basket-line-detail'),
    url(r'^lines/(?P<pk>[0-9]+)/$', LineDetail.as_view(), name='line-detail'),
    url(r'^lineattributes/(?P<pk>[0-9]+)/$', LineAttributeDetail.as_view(), name='lineattribute-detail'),
    url(r'^products/$', ProductList.as_view(), name='product-list'),
    url(r'^products/(?P<pk>[0-9]+)/$', ProductDetail.as_view(), name='product-detail'),
    url(r'^products/(?P<pk>[0-9]+)/price/$', ProductPrice.as_view(), name='product-price'),
    url(r'^products/(?P<pk>[0-9]+)/availability/$', ProductAvailability.as_view(), name='product-availability'),
    url(r'^products/(?P<pk>[0-9]+)/stockrecords/$', StockRecordList.as_view(), name='product-stockrecord-list'),
    url(r'^stockrecords/(?P<pk>[0-9]+)/$', StockRecordDetail.as_view(), name='stockrecord-detail'),
    url(r'^options/$', OptionList.as_view(), name='option-list'),
    url(r'^options/(?P<pk>[0-9]+)/$', OptionDetail.as_view(), name='option-detail'),
    url(r'^users/(?P<pk>[0-9]+)/$', UserDetail.as_view(), name='user-detail'),
    url(r'^checkout/$', CheckoutView.as_view(), name='api-checkout'),
    url(r'^orders/$', OrderList.as_view(), name='order-list'),
    url(r'^orders/(?P<pk>[0-9]+)/$', OrderDetail.as_view(), name='order-detail'),
    url(r'^orders/(?P<pk>[0-9]+)/lines/$', OrderLineList.as_view(), name='order-lines-list'),
    url(r'^orderlines/(?P<pk>[0-9]+)/$', OrderLineDetail.as_view(), name='order-lines-detail'),
    url(r'^orderlineattributes/(?P<pk>[0-9]+)/$', OrderLineAttributeDetail.as_view(), name='order-lineattributes-detail'),
    url(r'^countries/$', CountryList.as_view(), name='country-list'),
    url(r'^countries/(?P<pk>[A-z]+)/$', CountryDetail.as_view(), name='country-detail'),
    url(r'^partners/(?P<pk>[0-9]+)/$', PartnerDetail.as_view(), name='partner-detail'),
    url(r'^useraddresses/(?P<pk>[0-9]+)/$', UserAddressDetail.as_view(), name='useraddress-detail')
]

admin_urlpatterns = [
    url(r'^admin/baskets/$', BasketList.as_view(), name='basket-list'),
    url(r'^admin/lines/$', LineList.as_view(), name='line-list'),
    url(r'^admin/lineattributes/$', LineAttributeList.as_view(), name='lineattribute-list'),
    url(r'^admin/stockrecords/$', StockRecordList.as_view(), name='stockrecord-list'),
    url(r'^admin/users/$', UserList.as_view(), name='user-list'),
    url(r'^admin/partners/$', PartnerList.as_view(), name='partner-list'),
    url(r'^admin/useraddresses/$', UserAddressList.as_view(), name='useraddress-list'),
]

urlpatterns = format_suffix_patterns(urlpatterns + admin_urlpatterns)
