from rest_framework import generics
from rest_framework.response import Response

from oscar.core.loading import get_class, get_model

from oscarapi.utils.loading import get_api_classes, get_api_class


Selector = get_class("partner.strategy", "Selector")
(
    CategorySerializer,
    ProductLinkSerializer,
    ProductSerializer,
    AvailabilitySerializer,
) = get_api_classes(
    "serializers.product",
    [
        "CategorySerializer",
        "ProductLinkSerializer",
        "ProductSerializer",
        "AvailabilitySerializer",
    ],
)

PriceSerializer = get_api_class("serializers.checkout", "PriceSerializer")

__all__ = ("ProductList", "ProductDetail", "ProductPrice", "ProductAvailability")

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductLinkSerializer

    def get_queryset(self):
        """
        Allow filtering on structure so standalone and parent products can
        be selected separately, eg::

            http://127.0.0.1:8000/api/products/?structure=standalone

        or::

            http://127.0.0.1:8000/api/products/?structure=parent
        """
        qs = super(ProductList, self).get_queryset()
        structure = self.request.query_params.get("structure")
        if structure is not None:
            return qs.filter(structure=structure)

        return qs


class ProductDetail(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductPrice(generics.RetrieveAPIView):
    queryset = Product.objects.all()

    def get(self, request, pk=None, format=None):
        product = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = PriceSerializer(
            strategy.fetch_for_product(product).price, context={"request": request}
        )
        return Response(ser.data)


class ProductAvailability(generics.RetrieveAPIView):
    queryset = Product.objects.all()

    def get(self, request, pk=None, format=None):
        product = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = AvailabilitySerializer(
            strategy.fetch_for_product(product).availability,
            context={"request": request},
        )
        return Response(ser.data)


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryDetail(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
