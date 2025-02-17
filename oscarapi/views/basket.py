# pylint: disable=W0632
from django.utils.translation import gettext_lazy as _
from oscarapi.permissions import IsOwner

from oscar.apps.basket import signals
from oscar.core.loading import get_model, get_class

from rest_framework import status, generics, exceptions
from rest_framework.response import Response
from rest_framework.views import APIView

from oscarapi import permissions
from oscarapi.basket import operations
from oscarapi.utils.loading import get_api_classes, get_api_class
from oscarapi.views.utils import BasketPermissionMixin
from rest_framework.permissions import IsAuthenticated ,AllowAny
from oscar.core.loading import get_model
from server.apps.voucher.models import Voucher
from django.core.exceptions import PermissionDenied

Store = get_model('stores', 'Store')

__all__ = (
    "BasketView",
    "LineList",
    "AddProductView",
    "BasketLineDetail",
    "AddVoucherView",
    "ShippingMethodView",
)

Basket = get_model("basket", "Basket")
Line = get_model("basket", "Line")
Repository = get_class("shipping.repository", "Repository")
ShippingAddress = get_model("order", "ShippingAddress")
(  # pylint: disable=unbalanced-tuple-unpacking
    BasketSerializer,
    VoucherAddSerializer,
    VoucherSerializer,
    BasketLineSerializer,
) = get_api_classes(
    "serializers.basket",
    [
        "BasketSerializer",
        "VoucherAddSerializer",
        "VoucherSerializer",
        "BasketLineSerializer",
    ],
)
AddProductSerializer = get_api_class("serializers.product", "AddProductSerializer")
(
    ShippingAddressSerializer,
    ShippingMethodSerializer,
) = get_api_classes(  # pylint: disable=unbalanced-tuple-unpacking
    "serializers.checkout", ["ShippingAddressSerializer", "ShippingMethodSerializer"]
)


class BasketView(APIView):
    """
    API for retrieving a user's basket.

    GET:
    Retrieve your basket.
    """

    serializer_class = BasketSerializer
    permission_classes = [AllowAny]  # Ensure the user is authenticated

    def get(self, request, *args, **kwargs):
        basket = operations.get_basket(request)
        serializer = self.serializer_class(basket, context={"request": request})
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        """
        Delete all lines from the basket.
        """
        basket = operations.get_basket(request)
        
        # Check if the basket is frozen
        if basket.status == basket.FROZEN:
            return Response(
                {"message":  _("Cannot delete lines from a frozen basket.")},
                status=403  # Forbidden
            )
        basket.lines.all().delete()
        basket._lines = None
        basket.branch=None
        
        basket.save()
        return Response(
            {"message":  _("All lines have been successfully deleted from the basket.")},
            status=204  # No Content
        )


class AddProductView(APIView):
    """
    Add a certain quantity of a product to the basket.
    POST(url, quantity)
    {
        "url": "http://testserver.org/oscarapi/products/209/",
        "quantity": 6
    }
    If you've got some options to configure for the product to add to the
    basket, you should pass the optional ``options`` property:
    {
        "url": "http://testserver.org/oscarapi/products/209/",
        "quantity": 6,
        "options": [{
            "option": "http://testserver.org/oscarapi/options/1/",
            "value": "some value"
        }]
    }
    """
    permission_classes = [AllowAny]

    add_product_serializer_class = AddProductSerializer
    serializer_class = BasketSerializer

    def validate(
        self, basket, branch_id, product, quantity, options
    ):  # pylint: disable=unused-argument
        basket.branch = Store.objects.get(id=branch_id)
        basket.save()
        availability = basket.strategy.fetch_for_product(product, branch_id).availability
        # Check if product is available at all
        if not availability.is_available_to_buy:
            return False, availability.message
        current_qty = basket.product_quantity(product)
        desired_qty = current_qty + quantity
        # Check if we can buy this quantity
        allowed, message = availability.is_purchase_permitted(desired_qty)
        if not allowed:
            return False, message
        # Check if there is a limit on amount
        allowed, message = basket.is_quantity_allowed(desired_qty)
        if not allowed:
            return False, message
        return True, None

    def post(self, request, *args, **kwargs):  # pylint: disable=redefined-builtin
        p_ser = self.add_product_serializer_class(
            data=request.data, context={"request": request}
        )
        if p_ser.is_valid():
            basket = operations.get_basket(request)
            product = p_ser.validated_data["url"]
            quantity = p_ser.validated_data["quantity"]
            options = p_ser.validated_data.get("options", [])
            branch_id = p_ser.validated_data.get("branch_id", [])
            confirm = p_ser.validated_data.get("confirm", False)  # Confirmation flag

            # Validate the product addition
            basket_valid, message = self.validate(basket, branch_id, product, quantity, options)
            if not basket_valid:
                return Response(
                    {"reason": message}, status=status.HTTP_406_NOT_ACCEPTABLE
                )

            # Check for branch mismatch
            if basket.lines.exists():
                first_line = basket.lines.first()
                existing_stockrecord = first_line.stockrecord  # StockRecord of the first item in the cart
                existing_branch = existing_stockrecord.branch.id  # Branch of the first item in the cart
                
                if existing_branch != branch_id:
                    if not confirm:
                        # Return a warning message requiring confirmation
                        return Response({
                            "message": _("Your cart contains items from a different branch. Confirm to clear the cart and add this item."),
                        }, status=status.HTTP_409_CONFLICT)

                    # User confirmed, flush the cart
                    basket.flush()

            # Add the product to the basket
            basket.add_product(product, quantity=quantity, options=options)
            signals.basket_addition.send(
                sender=self, product=product, user=request.user, request=request
            )
            operations.apply_offers(request, basket)

            # Serialize and return the updated basket
            ser = self.serializer_class(basket, context={"request": request})
            return Response(ser.data)

        return Response({"reason": p_ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)


class AddVoucherView(APIView):
    """
    Add a voucher to the basket, ensuring the voucher and basket belong to the same vendor.

    POST(vouchercode)
    {
        "vouchercode": "kjadjhgadjgh7667"
    }

    Will return 200 and the updated basket if successful.
    If unsuccessful, will return 406 with the error.
    """
    permission_classes = [IsAuthenticated]
    add_voucher_serializer_class = VoucherAddSerializer
    serializer_class = VoucherSerializer

    def post(self, request, *args, **kwargs):
        v_ser = self.add_voucher_serializer_class(
            data=request.data, context={"request": request}
        )

        if v_ser.is_valid():
            basket = operations.get_basket(request)
            voucher = v_ser.instance

            # ✅ Step 1: Retrieve the Voucher's Vendor
            voucher_vendor = voucher.vendor if hasattr(voucher, "vendor") else None

            # ✅ Step 2: Retrieve the Basket's Vendor via Branch ID
            store_vendor = None
            if basket.branch:
                try:
                    store_vendor = basket.branch.vendor
                except Store.DoesNotExist:
                    return Response(
                        {"error": _("The associated branch/store does not exist.")},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # ✅ Step 3: Ensure the Voucher and Basket Have the Same Vendor
            if voucher_vendor and store_vendor and voucher_vendor != store_vendor:
                return Response(
                    {"error": _("Voucher code unknown.")},
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )

            # ✅ Step 4: Add the Voucher to the Basket
            basket.vouchers.add(voucher)
            signals.voucher_addition.send(sender=None, basket=basket, voucher=voucher)

            # ✅ Step 5: Apply Offers and Check Discounts
            operations.apply_offers(request, basket)
            discounts_after = basket.offer_applications

            # ✅ Step 6: Check if the Voucher Applies Any Discount
            for discount in discounts_after:
                if discount["voucher"] and discount["voucher"] == voucher:
                    break
            else:
                basket.vouchers.remove(voucher)
                return Response(
                    {"error": _("Your basket does not qualify for a voucher discount.")},
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )

            # ✅ Step 7: Return the Updated Basket
            basket_data = BasketSerializer(basket, context={"request": request}).data
            return Response(basket_data, status=status.HTTP_200_OK)

        return Response(v_ser.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


class ShippingMethodView(APIView):
    """
    GET:
    Retrieve shipping methods available to the user, basket, request combination

    POST(shipping_address):
    {
        "country": "http://127.0.0.1:8000/oscarapi/countries/NL/",
        "first_name": "Henk",
        "last_name": "Van den Heuvel",
        "line1": "Roemerlaan 44",
        "line2": "",
        "line3": "",
        "line4": "Kroekingen",
        "notes": "Niet STUK MAKEN OK!!!!",
        "phone_number": "+31 26 370 4887",
        "postcode": "7777KK",
        "state": "Gerendrecht",
        "title": "Mr"
    }

    Post a shipping_address if your shipping methods are dependent on the
    address.
    """
    permission_classes = (IsOwner,)

    serializer_class = ShippingAddressSerializer
    shipping_method_serializer_class = ShippingMethodSerializer

    def _get(self, request, shipping_address=None):  # pylint: disable=redefined-builtin
        basket = operations.get_basket(request)
        shiping_methods = Repository().get_shipping_methods(
            basket=basket,
            user=request.user,
            shipping_addr=shipping_address,
            request=request,
        )
        ser = self.shipping_method_serializer_class(
            shiping_methods, many=True, context={"basket": basket}
        )
        return Response(ser.data)

    def get(self, request, *args, **kwargs):  # pylint: disable=redefined-builtin
        """
        Get the available shipping methods and their cost for this order.

        GET:
        A list of shipping method details and the prices.
        """
        return self._get(request)

    def post(self, request, *args, **kwargs):  # pylint: disable=redefined-builtin
        s_ser = self.serializer_class(data=request.data, context={"request": request})
        if s_ser.is_valid():
            shipping_address = ShippingAddress(**s_ser.validated_data)
            return self._get(request, shipping_address=shipping_address)

        return Response(s_ser.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


class LineList(BasketPermissionMixin, generics.ListCreateAPIView):
    """
    Api for adding lines to a basket.

    Permission will be checked,
    Regular users may only access their own basket,
    staff users may access any basket.

    GET:
    A list of basket lines.

    POST(basket, line_reference, product, stockrecord,
         quantity, price_currency, price_excl_tax, price_incl_tax):
    Add a line to the basket, example::

        {
            "basket": "http://127.0.0.1:8000/oscarapi/baskets/100/",
            "line_reference": "234_345",
            "product": "http://127.0.0.1:8000/oscarapi/products/209/",
            "stockrecord":
                "http://127.0.0.1:8000/ooscarapi/products/209/stockercords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0"
        }
    """

    permission_classes = (permissions.RequestAllowsAccessTo,)
    serializer_class = BasketLineSerializer
    queryset = Line.objects.all()

    def get_queryset(self):
        basket_pk = self.kwargs.get("pk")
        basket = self.check_basket_permission(self.request, basket_pk=basket_pk)
        prepped_basket = operations.assign_basket_strategy(basket, self.request)
        return prepped_basket.all_lines()

    # pylint: disable=W1113
    def post(
        self, request, pk, format=None, *args, **kwargs
    ):  # pylint: disable=redefined-builtin,arguments-differ
        data_basket = self.get_data_basket(request.data, format)
        self.check_basket_permission(request, basket=data_basket)

        url_basket = self.check_basket_permission(request, basket_pk=pk)

        if url_basket != data_basket:
            raise exceptions.NotAcceptable(
                _("Target basket inconsistent %s != %s")
                % (url_basket.pk, data_basket.pk)
            )
        return super(LineList, self).post(request, format=format)

class BasketLineDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Only the field `quantity` can be changed in this view.
    All other fields are readonly.
    """
    queryset = Line.objects.all()
    serializer_class = BasketLineSerializer
    permission_classes = (permissions.RequestAllowsAccessTo,)

    def get_queryset(self):
        basket_pk = self.kwargs.get("basket_pk")
        basket = generics.get_object_or_404(operations.editable_baskets(), pk=basket_pk)
        prepped_basket = operations.prepare_basket(basket, self.request)
        if operations.request_allows_access_to_basket(self.request, prepped_basket):
            return prepped_basket.all_lines()
        else:
            return self.queryset.none()

    def validate(self, basket, branch_id, product, quantity, options):  # pylint: disable=unused-argument
        """
        Validate whether the requested quantity can be added to the basket.
        """
        availability = basket.strategy.fetch_for_product(product, branch_id).availability
        basket.branch =  Store.objects.get(id=branch_id)

        # Check if the product is available at all
        if not availability.is_available_to_buy:
            return False, availability.message

        # Calculate the total desired quantity (current + requested)
        current_qty = basket.product_quantity(product)
        desired_qty = current_qty + quantity
        # Check if the desired quantity is permitted
        allowed, message = availability.is_purchase_permitted(quantity)
        if not allowed:
            return False, message

        # Check if the basket's quantity limit is exceeded
        allowed, message = basket.is_quantity_allowed(quantity)
        if not allowed:
            return False, message

        return True, None

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a basket line, including quantity and options.
        Return the updated basket object serialized with BasketSerializer.
        """
        instance = self.get_object()  # Get the basket line instance

        # Validate input using the serializer
        serializer = BasketLineSerializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract validated data
        new_quantity = serializer.validated_data.get("quantity", instance.quantity)
        new_options = serializer.validated_data.get("options", [])
        branch_id = request.data.get("branch_id")

        # Validate input for quantity
        if not isinstance(new_quantity, int) or new_quantity <= 0:
            return Response(
                {"error": _("Invalid quantity.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Perform stock validation
        basket = instance.basket
        product = instance.product
        options = list(instance.attributes.values("option", "value"))  # Current options
        basket_valid, message = self.validate(basket, branch_id, product, new_quantity, options)
        if not basket_valid:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        # Update the quantity
        instance.quantity = new_quantity

        # Update the options
        if new_options:
            # Clear existing attributes
            instance.attributes.all().delete()

            # Add new attributes based on the provided options
            for option_dict in new_options:
                option = option_dict["option"]
                value = option_dict["value"]
                instance.attributes.create(option=option, value=value)

        # Save the updated instance
        instance.save()

        # Recalculate basket totals (if necessary)
        operations.apply_offers(request, basket)

        # Serialize the updated basket
        basket_serializer = BasketSerializer(basket, context={"request": request})

        # Return the serialized basket object
        return Response(basket_serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, *args, **kwargs):
        """
        Override the delete method to provide a custom response.
        """
        instance = self.get_object()
        basket = instance.basket
        try:
            # Perform the deletion
            self.perform_destroy(instance)
            
            if basket.is_empty:
                basket.branch = None  # Set branch to null if the basket is empty
                basket.save(update_fields=["branch"])  # Save only the branch field to avoid unnecessary updates
            basket_serializer = BasketSerializer(basket, context={"request": request})

            # Return the serialized basket object
            return Response(basket_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            # Handle any unexpected errors during deletion
            return Response(
                {"error": _("An error occurred while deleting the basket line.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class RemoveVoucherView(APIView):
    """
    Remove a voucher from the basket.

    DELETE(vouchercode)
    {
        "vouchercode": "kjadjhgadjgh7667"
    }

    Will return 200 and the updated basket if successful.
    If unsuccessful, will return 404 or 406 with an error.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        vouchercode = request.data.get("vouchercode")

        if not vouchercode:
            return Response(
                {"error": _("Voucher code is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        basket = operations.get_basket(request)

        print("vouchercode: ", vouchercode)
        print("basket: ", basket)
        # ✅ Step 1: Retrieve the Voucher
        try:
            voucher = Voucher.objects.get(code=vouchercode.upper())
            print("voucher: ", voucher)

        except Voucher.DoesNotExist:
            return Response(
                {"error": _("Voucher not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ✅ Step 2: Check if the Voucher is in the Basket
        if voucher not in basket.vouchers.all():
            return Response(
                {"error": _("The voucher is not in the basket.")},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        # ✅ Step 3: Retrieve Basket's Vendor via Branch
        store_vendor = None
        if basket.branch:
            try:
                store_vendor = basket.branch.vendor
            except Store.DoesNotExist:
                return Response(
                    {"error": _("The associated branch/store does not exist.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ✅ Step 4: Ensure the Voucher and Basket Have the Same Vendor
        if voucher.vendor and store_vendor and voucher.vendor != store_vendor:
            return Response(
                {"error": _("The voucher does not belong to the same vendor as the basket.")},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        # ✅ Step 5: Remove the Voucher from the Basket
        basket.vouchers.remove(voucher)

        # ✅ Step 6: Recalculate Discounts
        operations.apply_offers(request, basket)

        # ✅ Step 7: Return the Updated Basket
        basket_data = BasketSerializer(basket, context={"request": request}).data
        return Response(basket_data, status=status.HTTP_200_OK)