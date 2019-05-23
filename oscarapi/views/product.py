# pylint: disable=unbalanced-tuple-unpacking
from rest_framework import generics
from rest_framework.response import Response

from oscar.core.loading import get_class, get_model

from oscarapi.utils.loading import get_api_classes, get_api_class

create_from_breadcrumbs = get_class("catalogue.categories", "create_from_breadcrumbs")
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

    def get(
        self, request, pk=None, format=None
    ):  # pylint: disable=redefined-builtin,arguments-differ
        product = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = PriceSerializer(
            strategy.fetch_for_product(product).price, context={"request": request}
        )
        return Response(ser.data)


class ProductAvailability(generics.RetrieveAPIView):
    queryset = Product.objects.all()

    def get(
        self, request, pk=None, format=None
    ):  # pylint: disable=redefined-builtin,arguments-differ
        product = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = AvailabilitySerializer(
            strategy.fetch_for_product(product).availability,
            context={"request": request},
        )
        return Response(ser.data)


class CategoryList(generics.ListAPIView):
    queryset = Category.get_root_nodes()
    serializer_class = CategorySerializer

    def get_queryset(self):
        breadcrumb_path = self.kwargs.get("breadcrumbs", None)
        if breadcrumb_path is None:
            return super(CategoryList, self).get_queryset()

        return create_from_breadcrumbs(breadcrumb_path, separator="/").get_children()


class CategoryDetail(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
