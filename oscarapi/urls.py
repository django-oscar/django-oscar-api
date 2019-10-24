# pylint: disable=unbalanced-tuple-unpacking
from django.conf import settings
from django.urls import path, re_path
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
    BasketLineDetail,
) = get_api_classes(
    "views.basket",
    [
        "BasketView",
        "AddProductView",
        "AddVoucherView",
        "ShippingMethodView",
        "LineList",
        "BasketLineDetail",
    ],
)

(UserList, UserDetail) = get_api_classes("views.admin.user", ["UserList", "UserDetail"])
(StockRecordDetail, PartnerList, PartnerDetail) = get_api_classes(
    "views.admin.partner", ["StockRecordDetail", "PartnerList", "PartnerDetail"]
)

(
    BasketList,
    BasketDetail,
    LineAttributeDetail,
    OptionList,
    OptionDetail,
    CountryList,
    CountryDetail,
    RangeList,
    RangeDetail,
) = get_api_classes(
    "views.basic",
    [
        "BasketList",
        "BasketDetail",
        "LineAttributeDetail",
        "OptionList",
        "OptionDetail",
        "CountryList",
        "CountryDetail",
        "RangeList",
        "RangeDetail",
    ],
)

(
    ProductList,
    ProductDetail,
    ProductStockRecords,
    ProductStockRecordDetail,
    ProductPrice,
    ProductAvailability,
    CategoryList,
    CategoryDetail,
) = get_api_classes(
    "views.product",
    [
        "ProductList",
        "ProductDetail",
        "ProductStockRecords",
        "ProductStockRecordDetail",
        "ProductPrice",
        "ProductAvailability",
        "CategoryList",
        "CategoryDetail",
    ],
)

(
    CheckoutView,
    OrderList,
    OrderDetail,
    OrderLineList,
    OrderLineDetail,
    OrderLineAttributeDetail,
    UserAddressList,
    UserAddressDetail,
) = get_api_classes(
    "views.checkout",
    [
        "CheckoutView",
        "OrderList",
        "OrderDetail",
        "OrderLineList",
        "OrderLineDetail",
        "OrderLineAttributeDetail",
        "UserAddressList",
        "UserAddressDetail",
    ],
)

(
    ProductAdminList,
    ProductAdminDetail,
    ProductClassAdminList,
    ProductClassAdminDetail,
    ProductAttributeAdminList,
    ProductAttributeAdminDetail,
    AttributeOptionGroupAdminList,
    AttributeOptionGroupAdminDetail,
    CategoryAdminList,
    CategoryAdminDetail,
) = get_api_classes(
    "views.admin.product",
    [
        "ProductAdminList",
        "ProductAdminDetail",
        "ProductClassAdminList",
        "ProductClassAdminDetail",
        "ProductAttributeAdminList",
        "ProductAttributeAdminDetail",
        "AttributeOptionGroupAdminList",
        "AttributeOptionGroupAdminDetail",
        "CategoryAdminList",
        "CategoryAdminDetail",
    ],
)

(
    OrderAdminList,
    OrderAdminDetail,
    OrderLineAdminList,
    OrderLineAdminDetail,
    OrderLineAttributeAdminDetail,
) = get_api_classes(
    "views.admin.order",
    [
        "OrderAdminList",
        "OrderAdminDetail",
        "OrderLineAdminList",
        "OrderLineAdminDetail",
        "OrderLineAttributeAdminDetail",
    ],
)


urlpatterns = [
    path("", api_root, name="api-root"),
    path("login/", LoginView.as_view(), name="api-login"),
    path("basket/", BasketView.as_view(), name="api-basket"),
    path(
        "basket/add-product/", AddProductView.as_view(), name="api-basket-add-product"
    ),
    path(
        "basket/add-voucher/", AddVoucherView.as_view(), name="api-basket-add-voucher"
    ),
    path(
        "basket/shipping-methods/",
        ShippingMethodView.as_view(),
        name="api-basket-shipping-methods",
    ),
    path("baskets/", BasketList.as_view(), name="basket-list"),
    path("baskets/<int:pk>/", BasketDetail.as_view(), name="basket-detail"),
    path("baskets/<int:pk>/lines/", LineList.as_view(), name="basket-lines-list"),
    path(
        "baskets/<int:basket_pk>/lines/<int:pk>/",
        BasketLineDetail.as_view(),
        name="basket-line-detail",
    ),
    path(
        "baskets/<int:basket_pk>/lines/<int:line_pk>/lineattributes/<int:pk>/",
        LineAttributeDetail.as_view(),
        name="lineattribute-detail",
    ),
    path("products/", ProductList.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetail.as_view(), name="product-detail"),
    path("products/<int:pk>/price/", ProductPrice.as_view(), name="product-price"),
    path(
        "products/<int:pk>/availability/",
        ProductAvailability.as_view(),
        name="product-availability",
    ),
    path(
        "products/<int:pk>/stockrecords/",
        ProductStockRecords.as_view(),
        name="product-stockrecords",
    ),
    path(
        "products/<int:product_pk>/stockrecords/<int:pk>/",
        ProductStockRecordDetail.as_view(),
        name="product-stockrecord-detail",
    ),
    path("options/", OptionList.as_view(), name="option-list"),
    path("options/<int:pk>/", OptionDetail.as_view(), name="option-detail"),
    path("ranges/", RangeList.as_view(), name="range-list"),
    path("ranges/<int:pk>/", RangeDetail.as_view(), name="range-detail"),
    path("categories/", CategoryList.as_view(), name="category-list"),
    path("categories/<int:pk>/", CategoryDetail.as_view(), name="category-detail"),
    re_path(
        "^categories/(?P<breadcrumbs>.*)/$",
        CategoryList.as_view(),
        name="category-child-list",
    ),
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    path("checkout/", CheckoutView.as_view(), name="api-checkout"),
    path("orders/", OrderList.as_view(), name="order-list"),
    path("orders/<int:pk>/", OrderDetail.as_view(), name="order-detail"),
    path("orders/<int:pk>/lines/", OrderLineList.as_view(), name="order-lines-list"),
    path("orderlines/<int:pk>/", OrderLineDetail.as_view(), name="order-lines-detail"),
    path(
        "orderlineattributes/<int:pk>/",
        OrderLineAttributeDetail.as_view(),
        name="order-lineattributes-detail",
    ),
    path("countries/", CountryList.as_view(), name="country-list"),
    re_path(
        r"^countries/(?P<pk>[A-z]{2})/$", CountryDetail.as_view(), name="country-detail"
    ),
    path("useraddresses/", UserAddressList.as_view(), name="useraddress-list"),
    path(
        "useraddresses/<int:pk>/",
        UserAddressDetail.as_view(),
        name="useraddress-detail",
    ),
]

admin_urlpatterns = [
    path("admin/products/", ProductAdminList.as_view(), name="admin-product-list"),
    path(
        "admin/products/<int:pk>/",
        ProductAdminDetail.as_view(),
        name="admin-product-detail",
    ),
    path(
        "admin/productclasses/",
        ProductClassAdminList.as_view(),
        name="admin-productclass-list",
    ),
    path(
        "admin/productclasses/<slug:slug>/",
        ProductClassAdminDetail.as_view(),
        name="admin-productclass-detail",
    ),
    path("admin/categories/", CategoryAdminList.as_view(), name="admin-category-list"),
    path(
        "admin/categories/<int:pk>/",
        CategoryAdminDetail.as_view(),
        name="admin-category-detail",
    ),
    re_path(
        r"^admin/categories/(?P<breadcrumbs>.*)/$",
        CategoryAdminList.as_view(),
        name="admin-category-child-list",
    ),
    path(
        "admin/productattributes/",
        ProductAttributeAdminList.as_view(),
        name="admin-productattribute-list",
    ),
    path(
        "admin/stockrecords/<int:pk>/",
        StockRecordDetail.as_view(),
        name="admin-stockrecord-detail",
    ),
    path("admin/partners/", PartnerList.as_view(), name="partner-list"),
    path("admin/partners/<int:pk>/", PartnerDetail.as_view(), name="partner-detail"),
    path(
        "admin/productattributes/<int:pk>/",
        ProductAttributeAdminDetail.as_view(),
        name="admin-productattribute-detail",
    ),
    path(
        "admin/attributeoptiongroups/",
        AttributeOptionGroupAdminList.as_view(),
        name="admin-attributeoptiongroup-list",
    ),
    path(
        "admin/attributeoptiongroups/<int:pk>/",
        AttributeOptionGroupAdminDetail.as_view(),
        name="admin-attributeoptiongroup-detail",
    ),
    path("admin/orders/", OrderAdminList.as_view(), name="admin-order-list"),
    path(
        "admin/orders/<int:pk>/", OrderAdminDetail.as_view(), name="admin-order-detail"
    ),
    path(
        "admin/orders/<int:pk>/lines/",
        OrderLineAdminList.as_view(),
        name="admin-order-lines-list",
    ),
    path(
        "admin/orderlines/<int:pk>/",
        OrderLineAdminDetail.as_view(),
        name="admin-order-lines-detail",
    ),
    path(
        "admin/orderlineattributes/<int:pk>/",
        OrderLineAttributeAdminDetail.as_view(),
        name="admin-order-lineattributes-detail",
    ),
    path("admin/users/", UserList.as_view(), name="user-list"),
]

if not getattr(settings, "OSCARAPI_BLOCK_ADMIN_API_ACCESS", True):
    urlpatterns = urlpatterns + admin_urlpatterns

urlpatterns = format_suffix_patterns(urlpatterns)
