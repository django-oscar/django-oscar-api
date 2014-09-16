import collections
from django.contrib import auth
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from oscar.core.loading import get_model


__all__ = ('api_root',)

def PUBLIC_APIS(request, format): 
    return [
        ('login', reverse('api-login', request=request, format=format)),
        ('basket', reverse('api-basket', request=request, format=format)),
        ('basket-add-product', reverse('api-basket-add-product', request=request, format=format)),
        ('products', reverse('product-list', request=request, format=format)),
    ]

def PROTECTED_APIS(request, format):
    return [
        ('baskets', reverse('basket-list', request=request, format=format)),
        ('lines', reverse('line-list', request=request, format=format)),
        ('lineattributes', reverse('lineattribute-list', request=request, format=format)),
        ('options', reverse('option-list', request=request, format=format)),
        ('stockrecords', reverse('stockrecord-list', request=request, format=format)),
        ('users', reverse('user-list', request=request, format=format)),
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
