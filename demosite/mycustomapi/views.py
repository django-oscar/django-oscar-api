from oscarapi.views import basic

from .serializers import MyProductListSerializer


class ProductList(basic.ProductList):
    serializer_class = MyProductListSerializer
