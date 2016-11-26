from oscarapi.views import basic

from .serializers import MyProductLinkSerializer


class ProductList(basic.ProductList):
    serializer_class = MyProductLinkSerializer
