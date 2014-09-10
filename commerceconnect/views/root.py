from django.contrib import auth
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from oscar.core.loading import get_model


__all__ = ('api_root',)


@api_view(('GET',))
def api_root(request, format=None):
    return Response({
        'login': reverse('api-login', request=request, format=format),
        'baskets': reverse('basket-list', request=request, format=format),
        'lines': reverse('line-list', request=request, format=format),
        'lineattributes': reverse('lineattribute-list', request=request, format=format),
        'products': reverse('product-list', request=request, format=format),
        'stockrecords': reverse('stockrecord-list', request=request, format=format),
        'users': reverse('user-list', request=request, format=format),
        
    })
