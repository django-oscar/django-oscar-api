from oscarapi.views import product

from .serializers import MyProductLinkSerializer


class ProductList(product.ProductList):
    serializer_class = MyProductLinkSerializer
