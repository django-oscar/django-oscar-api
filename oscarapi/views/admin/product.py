# pylint: disable=unbalanced-tuple-unpacking
from rest_framework import generics

from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_classes, get_api_class


APIAdminPermission = get_api_class("permissions", "APIAdminPermission")
ProductAttributeSerializer, AttributeOptionGroupSerializer = get_api_classes(
    "serializers.product",
    ["ProductAttributeSerializer", "AttributeOptionGroupSerializer"],
)
AdminProductSerializer, AdminCategorySerializer, AdminProductClassSerializer, = get_api_classes(
    "serializers.admin.product",
    [
        "AdminProductSerializer",
        "AdminCategorySerializer",
        "AdminProductClassSerializer",
    ],
)
CategoryList = get_api_class("views.product", "CategoryList")
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductClass = get_model("catalogue", "ProductClass")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")


class ProductAdminList(generics.ListCreateAPIView):
    serializer_class = AdminProductSerializer
    queryset = Product.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class ProductAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminProductSerializer
    queryset = Product.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class ProductClassAdminList(generics.ListCreateAPIView):
    serializer_class = AdminProductClassSerializer
    queryset = ProductClass.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class ProductClassAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminProductClassSerializer
    queryset = ProductClass.objects.get_queryset()
    permission_classes = (APIAdminPermission,)
    lookup_field = "slug"


class ProductAttributeAdminList(generics.ListCreateAPIView):
    serializer_class = ProductAttributeSerializer
    queryset = ProductAttribute.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class ProductAttributeAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductAttributeSerializer
    queryset = ProductAttribute.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class AttributeOptionGroupAdminList(generics.ListCreateAPIView):
    serializer_class = AttributeOptionGroupSerializer
    queryset = AttributeOptionGroup.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class AttributeOptionGroupAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AttributeOptionGroupSerializer
    queryset = AttributeOptionGroup.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class CategoryAdminList(generics.ListCreateAPIView, CategoryList):
    queryset = Category.get_root_nodes()
    serializer_class = AdminCategorySerializer
    permission_classes = (APIAdminPermission,)

    def get_serializer_context(self):
        ctx = super(CategoryAdminList, self).get_serializer_context()
        breadcrumb_path = self.kwargs.get("breadcrumbs", None)

        if breadcrumb_path is not None:
            ctx["breadcrumbs"] = breadcrumb_path

        return ctx


class CategoryAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = AdminCategorySerializer
    permission_classes = (APIAdminPermission,)
