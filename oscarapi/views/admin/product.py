# pylint: disable=unbalanced-tuple-unpacking
from django.http import Http404
from rest_framework import generics
from rest_framework.exceptions import NotFound

from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_classes, get_api_class
from oscarapi.utils.exists import construct_id_filter

APIAdminPermission = get_api_class("permissions", "APIAdminPermission")
ProductAttributeSerializer, AttributeOptionGroupSerializer = get_api_classes(
    "serializers.product",
    ["ProductAttributeSerializer", "AttributeOptionGroupSerializer"],
)
(
    AdminProductSerializer,
    AdminCategorySerializer,
    AdminProductClassSerializer,
) = get_api_classes(
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


class ProductAdminList(generics.UpdateAPIView, generics.ListCreateAPIView):
    """
    Use this api for synchronizing data from another datasource.

    This api endpoint supports POST, PUT and PATCH, which means it can be used
    for creating, but also for updating. There is no need to supply the
    primary key(id) of the product, as long as you are sending enough data
    to uniquely identify the product (upc). That means you can try updating and
    if that fails, try POST. Or the other way around, whatever makes most
    sense in you scenario.

    Note that if you have changed the product model and changed upc to no longer
    be unique, you MUST add another unique field or specify a unique together
    constraint. And you have to send that data along.
    """

    serializer_class = AdminProductSerializer
    queryset = Product.objects.get_queryset()
    permission_classes = (APIAdminPermission,)

    def get_object(self):
        """
        Returns the object the view is displaying.

        Tries to extract a uniquely identifying query from the posted data
        """
        try:
            automatic_filter = construct_id_filter(Product, self.request.data)
            if automatic_filter:
                obj = Product.objects.get(automatic_filter)
                self.check_object_permissions(self.request, obj)
                return obj
            else:
                raise NotFound(
                    "Not enough info to identify %s." % Product._meta.object_name
                )
        except Product.DoesNotExist:
            raise Http404("No %s matches the given query." % Product._meta.object_name)


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

    def get_queryset(self):
        try:
            return super(CategoryAdminList, self).get_queryset()
        except NotFound:  # admins might be able to create so hold the error.
            return Category.objects.none()

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
