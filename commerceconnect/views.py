from django.conf import settings
from django.contrib import auth
from oscar.core.loading import get_model
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from commerceconnect import serializers
from commerceconnect.utils import login_and_upgrade_session


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


class LoginView(APIView):
    """
    1. The user will be authenticated. The next steps will only be
       performed is login is succesful. Logging in logged in users results in 405.
    2. The anonymous cart will be merged with the private cart associated with that
       authenticated user.
    3. A new session will be started, this session identifies the authenticated user
       for the duration of the session, without further calls to gigya.
    4. The new, merged cart will be associated with this session.
    5. The anonymous session will be terminated.
    6. A response will be issued containing the new session id as a header (more on
       this later).
    """

    def get(self, request, format=None):
        if settings.DEBUG:
            if request.user.is_authenticated():
                ser = serializers.UserSerializer(request.user, many=False)
                return Response(ser.data)
            return Response(status=status.HTTP_204_NO_CONTENT)

        raise MethodNotAllowed('GET')

    def post(self, request, format=None):
        ser = serializers.LoginSerializer(data=request.DATA)
        if ser.is_valid():

            anonymous_basket = Basket.get_anonymous_basket(request)
            
            user = ser.object

            # refuse to login logged in users, to avoid attaching sessions to
            # multiple users at the same time.
            if request.user.is_authenticated():
                return Response({'detail':'Session is in use, log out first'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

            request.user = user
        
            login_and_upgrade_session(request._request, user)

            # merge anonymous basket with authenticated basket.
            basket = Basket.get_user_basket(user)
            if anonymous_basket is not None:
                basket.merge(anonymous_basket)
                anonymous_basket.delete()
            basket.store_basket(request)

            return Response()

        return Response(ser.errors, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, format=None):
        """
        Destroy the session.
        
        for anonymous users that means having their basket destroyed as well,
        because there is no way to reach it otherwise.
        """
        request = request._request
        if request.user.is_anonymous():
            basket = Basket.get_anonymous_basket(request)
            if basket:
                basket.delete()

        request.session.clear()
        request.session.delete()
        request.session = None

        return Response()
