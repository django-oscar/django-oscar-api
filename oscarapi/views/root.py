import collections

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


__all__ = ("api_root",)


def PUBLIC_APIS(r, f):
    return [
        ("login", reverse("api-login", request=r, format=f)),
        ("basket", reverse("api-basket", request=r, format=f)),
        ("basket-add-product", reverse("api-basket-add-product", request=r, format=f)),
        ("basket-add-voucher", reverse("api-basket-add-voucher", request=r, format=f)),
        (
            "basket-shipping-methods",
            reverse("api-basket-shipping-methods", request=r, format=f),
        ),
        ("baskets", reverse("basket-list", request=r, format=f)),
        ("categories", reverse("category-list", request=r, format=f)),
        ("checkout", reverse("api-checkout", request=r, format=f)),
        ("orders", reverse("order-list", request=r, format=f)),
        ("options", reverse("option-list", request=r, format=f)),
        ("products", reverse("product-list", request=r, format=f)),
        ("countries", reverse("country-list", request=r, format=f)),
        ("useraddresses", reverse("useraddress-list", request=r, format=f)),
    ]


def STAFF_APIS(r, f):
    return [
        ("users", reverse("user-list", request=r, format=f)),
    ]


def ADMIN_APIS(r, f):
    return [
        ("productclasses", reverse("admin-productclass-list", request=r, format=f)),
        ("products", reverse("admin-product-list", request=r, format=f)),
        ("categories", reverse("admin-category-list", request=r, format=f)),
        ("orders", reverse("admin-order-list", request=r, format=f)),
        ("partners", reverse("partner-list", request=r, format=f)),
    ]


@api_view(("GET",))
def api_root(request, format=None):  # pylint: disable=redefined-builtin
    """
    GET:
    Display all available urls.

    Since some urls have specific permissions, you might not be able to access
    them all.
    """
    apis = PUBLIC_APIS(request, format)

    if request.user.is_staff:
        apis += [
            ("staff", collections.OrderedDict(STAFF_APIS(request, format))),
            ("admin", collections.OrderedDict(ADMIN_APIS(request, format))),
        ]

    return Response(collections.OrderedDict(apis))
