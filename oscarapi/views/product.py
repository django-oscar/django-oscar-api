# pylint: disable=unbalanced-tuple-unpacking
from rest_framework import generics
from rest_framework.response import Response

from oscar.core.loading import get_class, get_model

from oscarapi.utils.categories import find_from_full_slug
from oscarapi.utils.loading import get_api_classes, get_api_class

Selector = get_class("partner.strategy", "Selector")
(
    CategorySerializer,
    ProductLinkSerializer,
    ProductSerializer,
    ProductStockRecordSerializer,
    AvailabilitySerializer,
) = get_api_classes(
    "serializers.product",
    [
        "CategorySerializer",
        "ProductLinkSerializer",
        "ProductSerializer",
        "ProductStockRecordSerializer",
        "AvailabilitySerializer",
    ],
)

PriceSerializer = get_api_class("serializers.checkout", "PriceSerializer")


__all__ = ("ProductList", "ProductDetail", "ProductPrice", "ProductAvailability")

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
StockRecord = get_model("partner", "StockRecord")


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
    serializer_class = PriceSerializer

    def get(
        self, request, *args, **kwargs
    ):  # pylint: disable=redefined-builtin,arguments-differ
        product = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = PriceSerializer(
            strategy.fetch_for_product(product).price, context={"request": request}
        )
        return Response(ser.data)


class ProductStockRecords(generics.ListAPIView):
    serializer_class = ProductStockRecordSerializer
    queryset = StockRecord.objects.all()

    def get_queryset(self):
        product_pk = self.kwargs.get("pk")
        return super().get_queryset().filter(product_id=product_pk)


class ProductStockRecordDetail(generics.RetrieveAPIView):
    serializer_class = ProductStockRecordSerializer
    queryset = StockRecord.objects.all()


class ProductAvailability(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = AvailabilitySerializer

    def get(
        self, request, *args, **kwargs
    ):  # pylint: disable=redefined-builtin,arguments-differ
        product = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = AvailabilitySerializer(
            strategy.fetch_for_product(product).availability,
            context={"request": request},
        )
        return Response(ser.data)


class CategoryList(generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        """
        Fetches the root nodes or children of a category filtered by vendor if provided.
        """
        breadcrumb_path = self.kwargs.get("breadcrumbs", None)
        vendor_id = self.request.query_params.get("vendor", None)

        # Get root nodes or filter by breadcrumbs
        if breadcrumb_path:
            category = find_from_full_slug(breadcrumb_path, separator="/")
            queryset = category.get_children()
        else:
            queryset = Category.get_root_nodes()

        # Filter by vendor if vendor_id is provided
        if vendor_id:
            queryset = queryset.filter(vendor__id=vendor_id)

        return queryset



class CategoryDetail(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
