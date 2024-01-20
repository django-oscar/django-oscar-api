"""
All oscarapi settings are defined in :mod:`oscarapi.settings`.

To set these settings in you django `settings.py` file, prefix them with
`OSCARAPI_`. So :const:`oscarapi.settings.EXPOSE_USER_DETAILS` becomes:
`OSCARAPI_EXPOSE_USER_DETAILS`
"""

from django.contrib.auth import get_user_model
from oscarapi.utils.settings import overridable
from oscarapi import version

User = get_user_model()


#: :const: OSCARAPI_BLOCK_ADMIN_API_ACCESS is useful in production websites where you
#: want to make sure that the admin api is not exposed at all.
BLOCK_ADMIN_API_ACCESS = overridable("OSCARAPI_BLOCK_ADMIN_API_ACCESS", True)

#: OSCARAPI_EXPOSE_USER_DETAILS
#: The ``Login`` view (``GET``) and the ``owner`` field in the
#: ``BasketSerializer`` and ``CheckoutSerializer`` expose user details, like
#: username and email address. With this setting you can enable/disable this behaviour.
EXPOSE_USER_DETAILS = overridable("OSCARAPI_EXPOSE_USER_DETAILS", False)

#: Enables the ``register`` endpoint so it's possible to create new user accounts.
ENABLE_REGISTRATION = overridable("OSCARAPI_ENABLE_REGISTRATION", False)

#: Changes the headers for the admin api when downloading images.
LAZY_REMOTE_FILE_REQUEST_HEADERS = overridable(
    "OSCARAPI_LAZY_REMOTE_FILE_REQUEST_HEADERS",
    default={"User-Agent": f"django-oscar-api/{version}"},
)

FILE_DOWNLOADER_MODULE = overridable(
    "OSCARAPI_FILE_DOWNLOADER_MODULE", default="download.default"
)


VOUCHER_FIELDS = overridable(
    "OSCARAPI_VOUCHER_FIELDS",
    default=("name", "code", "start_datetime", "end_datetime"),
)

BASKET_FIELDS = overridable(
    "OSCARAPI_BASKET_FIELDS",
    default=(
        "id",
        "owner",
        "status",
        "lines",
        "url",
        "total_excl_tax",
        "total_excl_tax_excl_discounts",
        "total_incl_tax",
        "total_incl_tax_excl_discounts",
        "total_tax",
        "currency",
        "voucher_discounts",
        "offer_discounts",
        "is_tax_known",
    ),
)
BASKETLINE_FIELDS = overridable(
    "OSCARAPI_BASKETLINE_FIELDS",
    default=(
        "url",
        "product",
        "quantity",
        "attributes",
        "price_currency",
        "price_excl_tax",
        "price_incl_tax",
        "price_incl_tax_excl_discounts",
        "price_excl_tax_excl_discounts",
        "is_tax_known",
        "warning",
        "basket",
        "stockrecord",
        "date_created",
        "date_updated",
    ),
)

ORDERLINE_FIELDS = overridable(
    "OSCARAPI_ORDERLINE_FIELDS",
    default=(
        "attributes",
        "url",
        "product",
        "stockrecord",
        "quantity",
        "price_currency",
        "price_excl_tax",
        "price_incl_tax",
        "price_incl_tax_excl_discounts",
        "price_excl_tax_excl_discounts",
        "order",
    ),
)
SURCHARGE_FIELDS = overridable(
    "OSCARAPI_SURCHARGE_FIELDS",
    default=("name", "code", "incl_tax", "excl_tax"),
)
ORDER_FIELDS = overridable(
    "OSCARAPI_ORDER_FIELDS",
    default=(
        "number",
        "basket",
        "url",
        "lines",
        "owner",
        "billing_address",
        "currency",
        "total_incl_tax",
        "total_excl_tax",
        "shipping_incl_tax",
        "shipping_excl_tax",
        "shipping_address",
        "shipping_method",
        "shipping_code",
        "status",
        "email",
        "date_placed",
        "payment_url",
        "offer_discounts",
        "voucher_discounts",
        "surcharges",
    ),
)
INITIAL_ORDER_STATUS = overridable("OSCARAPI_INITIAL_ORDER_STATUS", default="new")
USERADDRESS_FIELDS = overridable(
    "OSCARAPI_USERADDRESS_FIELDS",
    default=(
        "id",
        "title",
        "first_name",
        "last_name",
        "line1",
        "line2",
        "line3",
        "line4",
        "state",
        "postcode",
        "search_text",
        "phone_number",
        "notes",
        "is_default_for_shipping",
        "is_default_for_billing",
        "country",
        "url",
    ),
)
USER_FIELDS = overridable(
    "OSCARAPI_USER_FIELDS",
    default=(User.USERNAME_FIELD, "email", "date_joined"),
)
OPTION_FIELDS = overridable("OSCARAPI_OPTION_FIELDS", default="__all__")
PRODUCT_ATTRIBUTE_VALUE_FIELDS = overridable(
    "OSCARAPI_PRODUCT_ATTRIBUTE_VALUE_FIELDS",
    default=("name", "value", "code", "product"),
)
RECOMMENDED_PRODUCT_FIELDS = overridable(
    "OSCARAPI_RECOMMENDED_PRODUCT_FIELDS", default=("url",)
)
CHILDPRODUCTDETAIL_FIELDS = overridable(
    "OSCARAPI_CHILDPRODUCTDETAIL_FIELDS",
    default=(
        "url",
        "upc",
        "id",
        "title",
        "structure",
        # 'parent', 'description', 'images', are not included by default, but
        # easily enabled by overriding OSCARAPI_CHILDPRODUCTDETAIL_FIELDS
        # in your settings file
        "date_created",
        "date_updated",
        "recommended_products",
        "attributes",
        "categories",
        "product_class",
        "price",
        "availability",
        "options",
    ),
)
PRODUCTDETAIL_FIELDS = overridable(
    "OSCARAPI_PRODUCTDETAIL_FIELDS",
    default=(
        "url",
        "upc",
        "id",
        "title",
        "description",
        "structure",
        "date_created",
        "date_updated",
        "recommended_products",
        "attributes",
        "categories",
        "product_class",
        "images",
        "price",
        "availability",
        "stockrecords",
        "options",
        "children",
    ),
)
PRODUCT_FIELDS = overridable(
    "OSCARAPI_PRODUCT_FIELDS", default=("url", "id", "upc", "title")
)
ADMIN_USER_FIELDS = overridable(
    "OSCARAPI_ADMIN_USER_FIELDS",
    default=("url", User.USERNAME_FIELD, "email", "date_joined"),
)
