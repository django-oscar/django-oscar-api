from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_classes
from oscarapi.views.mixin import PutIsPatchMixin


ProductAttributeSerializer, AttributeOptionGroupSerializer = get_api_classes(
    "serializers.product",
    ["ProductAttributeSerializer", "AttributeOptionGroupSerializer"],
)
AdminProductSerializer, AdminProductClassSerializer, = get_api_classes(
    "serializers.admin.product",
    ["AdminProductSerializer", "AdminProductClassSerializer"],
)
Product = get_model("catalogue", "Product")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductClass = get_model("catalogue", "ProductClass")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")


class ProductAdminList(PutIsPatchMixin, generics.ListCreateAPIView):
    serializer_class = AdminProductSerializer
    queryset = Product.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class ProductAdminDetail(PutIsPatchMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminProductSerializer
    queryset = Product.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class ProductClassAdminList(PutIsPatchMixin, generics.ListCreateAPIView):
    serializer_class = AdminProductClassSerializer
    queryset = ProductClass.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class ProductClassAdminDetail(PutIsPatchMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminProductClassSerializer
    queryset = ProductClass.objects.get_queryset()
    permission_classes = (IsAdminUser,)
    lookup_field = "slug"


class ProductAttributeAdminList(PutIsPatchMixin, generics.ListCreateAPIView):
    serializer_class = ProductAttributeSerializer
    queryset = ProductAttribute.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class ProductAttributeAdminDetail(
    PutIsPatchMixin, generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = ProductAttributeSerializer
    queryset = ProductAttribute.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class AttributeOptionGroupAdminList(generics.ListCreateAPIView):
    serializer_class = AttributeOptionGroupSerializer
    queryset = AttributeOptionGroup.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class AttributeOptionGroupAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AttributeOptionGroupSerializer
    queryset = AttributeOptionGroup.objects.get_queryset()
    permission_classes = (IsAdminUser,)
