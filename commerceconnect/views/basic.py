from django.contrib import auth
from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from commerceconnect import serializers, permissions
from oscar.core.loading import get_model


__all__ = (
    'BasketList', 'BasketDetail',
    'LineAttributeList', 'LineAttributeDetail',
    'ProductList', 'ProductDetail',
    'StockRecordList', 'StockRecordDetail',
    'UserList', 'UserDetail',
    'OptionList', 'OptionDetail'
)

Basket = get_model('basket', 'Basket')
LineAttribute = get_model('basket', 'LineAttribute')
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')
Option = get_model('catalogue', 'Option')
User = auth.get_user_model()


class BasketList(generics.ListCreateAPIView):
    queryset = Basket.objects.all()
    serializer_class = serializers.BasketSerializer
    permission_classes = (IsAdminUser,)
class BasketDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Basket.objects.all()
    serializer_class = serializers.BasketSerializer
    permission_classes = (permissions.IsAdminUserOrRequestOwner,)


class LineAttributeList(generics.ListCreateAPIView):
    queryset = LineAttribute.objects.all()
    serializer_class = serializers.LineAttributeSerializer
class LineAttributeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = LineAttribute.objects.all()
    serializer_class = serializers.LineAttributeSerializer


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = serializers.ProductLinkSerializer
class ProductDetail(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = serializers.ProductSerializer


class StockRecordList(generics.ListAPIView):
    queryset = StockRecord.objects.all()
    serializer_class = serializers.StockRecordSerializer

    def get(self, request, pk=None, *args, **kwargs):
        if pk is not None:
            self.queryset = self.queryset.filter(product__id=pk)

        return super(StockRecordList, self).get(request, *args, **kwargs)
class StockRecordDetail(generics.RetrieveAPIView):
    queryset = StockRecord.objects.all()
    serializer_class = serializers.StockRecordSerializer


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (IsAdminUser,)
class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (IsAdminUser,)


class OptionList(generics.ListCreateAPIView):
    queryset = Option.objects.all()
    serializer_class = serializers.OptionSerializer
class OptionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Option.objects.all()
    serializer_class = serializers.OptionSerializer

