import collections

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


__all__ = ('api_root',)


def PUBLIC_APIS(r, f):
    return [
        ('login', reverse('api-login', request=r, format=f)),
        ('basket', reverse('api-basket', request=r, format=f)),
        ('basket-add-product', reverse('api-basket-add-product', request=r,
                                       format=f)),
        ('basket-add-voucher', reverse('api-basket-add-voucher', request=r,
                                       format=f)),
        ('basket-shipping-methods', reverse('api-basket-shipping-methods', request=r,
                                       format=f)),
        ('checkout', reverse('api-checkout', request=r, format=f)),
        ('orders', reverse('order-list', request=r, format=f)),
        ('products', reverse('product-list', request=r, format=f)),
        ('countries', reverse('country-list', request=r, format=f)),
    ]


def PROTECTED_APIS(r, f):
    return [
        ('baskets', reverse('basket-list', request=r, format=f)),
        ('lines', reverse('line-list', request=r, format=f)),
        ('lineattributes', reverse('lineattribute-list', request=r, format=f)),
        ('options', reverse('option-list', request=r, format=f)),
        ('stockrecords', reverse('stockrecord-list', request=r, format=f)),
        ('users', reverse('user-list', request=r, format=f)),
        ('partners', reverse('partner-list', request=r, format=f)),
    ]


@api_view(('GET',))
def api_root(request, format=None):
    """
    GET:
    Display all available urls.

    Since some urls have specific permissions, you might not be able to access
    them all.
    """
    apis = PUBLIC_APIS(request, format)
    if request.user.is_staff:
        apis += PROTECTED_APIS(request, format)

    return Response(collections.OrderedDict(apis))
