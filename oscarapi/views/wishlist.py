from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from oscar.core.loading import get_model
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import logging
from oscarapi.utils.loading import get_api_classes
from django.utils.translation import gettext as _

# Models and Serializers
Product = get_model("catalogue", "Product")
WishList = get_model("wishlists", "WishList")
Line = get_model("wishlists", "Line")
(WishListSerializer, LineSerializer) = get_api_classes(
    "serializers.wishlist",
    ["WishListSerializer", "LineSerializer"],
)

logger = logging.getLogger(__name__)

class WishlistView(GenericAPIView):
    """
    A consolidated API view to handle wishlist operations:
    - POST: Add a product to the wishlist.
    - GET: Retrieve the wishlist details with pagination.
    - DELETE: Remove a product from the wishlist.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LineSerializer

    def get_queryset(self):
        """
        Get the queryset of wishlist lines for the authenticated user,
        ordered with the most recent ones first.
        """
        try:
            wishlist = WishList.objects.get(owner=self.request.user, name="Default")
            return wishlist.lines.all().order_by("-id")
        except WishList.DoesNotExist:
            logger.warning(f"Wishlist not found for user {self.request.user}")
            return Line.objects.none()

    def _get_paginated_response(self, queryset):
        """
        Helper method to paginate and serialize the queryset.
        """
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Add a product to the user's wishlist.
        """
        product_id = request.data.get("product_id")
        if not product_id:
            return Response(
                {"error": _("Product ID is required")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(id=product_id)
        except ObjectDoesNotExist:
            return Response(
                {"error": _("Product not found")}, status=status.HTTP_404_NOT_FOUND
            )

        wishlist, _ = WishList.objects.get_or_create(
            owner=request.user, defaults={"name": "Default"}
        )

        try:
            wishlist.add(product)  # Assuming `add` is a method on the WishList model
            logger.info(
                f"Product ID {product_id} added to wishlist of user {request.user}"
            )
        except Exception as e:
            logger.error(f"Error adding product to wishlist: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Return updated wishlist
        return self._get_paginated_response(self.get_queryset())

    def get(self, request, *args, **kwargs):
        """
        Retrieve the user's wishlist details with pagination.
        """
        return self._get_paginated_response(self.get_queryset())

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        """
        Remove a product from the user's wishlist.
        """
        line_id = request.data.get("line_id")
        if not line_id:
            return Response(
                {"error": _("Line ID is required")}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            line = Line.objects.get(id=line_id, wishlist__owner=request.user)
        except Line.DoesNotExist:
            logger.warning(
                f"Attempt to delete non-existent line ID: {line_id} by user {request.user}"
            )
            return Response(
                {"error": _("Line not found or does not belong to the user")},
                status=status.HTTP_404_NOT_FOUND,
            )

        line.delete()
        logger.info(f"Line ID {line_id} deleted from wishlist of user {request.user}")

        # Return updated wishlist
        return self._get_paginated_response(self.get_queryset())