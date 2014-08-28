from django.db.models.loading import get_model
from django.shortcuts import render

from rest_framework import generics

from commerceconnect.serializers import *
from rest_framework import renderers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')
LineAttribute = get_model('basket', 'LineAttribute')
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')


@api_view(('GET',))
def api_root(request, format=None):
    return Response({
        'baskets': reverse('basket-list', request=request, format=format),
        'lines': reverse('line-list', request=request, format=format),
        'lineattributes': reverse('lineattribute-list', request=request, format=format),
        'products': reverse('product-list', request=request, format=format),
        'stockrecords': reverse('stockrecord-list', request=request, format=format),
    })


class BasketList(generics.ListCreateAPIView):
    queryset = Basket.objects.all()
    serializer_class = BasketSerializer
class BasketDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Basket.objects.all()
    serializer_class = BasketSerializer


class LineList(generics.ListCreateAPIView):
    queryset = Line.objects.all()
    serializer_class = LineSerializer
class LineDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Line.objects.all()
    serializer_class = LineSerializer


class LineAttributeList(generics.ListCreateAPIView):
    queryset = LineAttribute.objects.all()
    serializer_class = LineAttributeSerializer
class LineAttributeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = LineAttribute.objects.all()
    serializer_class = LineAttributeSerializer


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
class ProductDetail(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class StockRecordList(generics.ListAPIView):
    queryset = StockRecord.objects.all()
    serializer_class = StockRecordSerializer
class StockRecordDetail(generics.RetrieveAPIView):
    queryset = StockRecord.objects.all()
    serializer_class = StockRecordSerializer

