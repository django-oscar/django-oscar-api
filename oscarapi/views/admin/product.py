from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from oscar.core.loading import get_class, get_model
from oscarapi.utils.loading import get_api_classes, get_api_class

AdminProductSerializer = get_api_class("serializers.admin.product", "AdminProductSerializer")
Product = get_model("catalogue", "Product")


class ProductAdminList(generics.ListCreateAPIView):
    serializer_class = AdminProductSerializer
    queryset = Product.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class ProductAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminProductSerializer
    queryset = Product.objects.get_queryset()
    permission_classes = (IsAdminUser,)
