from django.contrib import auth
from oscar.core.loading import get_model
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from commerceconnect import serializers


Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')
LineAttribute = get_model('basket', 'LineAttribute')
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')
User = auth.get_user_model()


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


class BasketList(generics.ListCreateAPIView):
    queryset = Basket.objects.all()
    serializer_class = serializers.BasketSerializer
    permission_classes = (IsAdminUser,)
class BasketDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Basket.objects.all()
    serializer_class = serializers.BasketSerializer


class LineList(generics.ListCreateAPIView):
    queryset = Line.objects.all()
    serializer_class = serializers.LineSerializer
class LineDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Line.objects.all()
    serializer_class = serializers.LineSerializer


class LineAttributeList(generics.ListCreateAPIView):
    queryset = LineAttribute.objects.all()
    serializer_class = serializers.LineAttributeSerializer
class LineAttributeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = LineAttribute.objects.all()
    serializer_class = serializers.LineAttributeSerializer


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = serializers.ProductSerializer
class ProductDetail(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = serializers.ProductSerializer


class StockRecordList(generics.ListAPIView):
    queryset = StockRecord.objects.all()
    serializer_class = serializers.StockRecordSerializer
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


class LoginView(APIView):
    # no we don;t need to authenticate users that log in ok?
    authentication_classes = ()

    def post(self, request, format=None):
        ser = serializers.LoginSerializer(data=request.DATA)
        if ser.is_valid():
            user = ser.object
            request.user = user
            # make sure that auth.login doesn't create a new session key
            request.session[auth.SESSION_KEY] = user.pk
            auth.login(request, ser.object)
            request.session.save()
            return Response()

        return Response(ser.errors, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, format=None):
        request.session.clear()
        request.session.delete()
        return Response()
