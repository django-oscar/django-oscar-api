# pylint: disable=W0632
from oscar.core.loading import get_model

from rest_framework import generics, response, status, views

from oscarapi.basket.operations import request_allows_access_to_basket
from oscarapi.permissions import IsOwner
from oscarapi.utils.loading import get_api_classes
from oscarapi.signals import oscarapi_post_checkout
from oscarapi.views.utils import parse_basket_from_hyperlink
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from datetime import timedelta

from server.apps.service.holds import lock_service_slots
from server.apps.partner.availability import lock_stock_records
from oscar.apps.partner.strategy import Selector


Order = get_model("order", "Order")
OrderLine = get_model("order", "Line")
OrderLineAttribute = get_model("order", "LineAttribute")
UserAddress = get_model("address", "UserAddress")
Order = get_model('order', 'Order')


(
    CheckoutSerializer,
    OrderLineAttributeSerializer,
    OrderLineSerializer,
    OrderSerializer,
    UserAddressSerializer,
    OrderRatingPopupSerializer,
    DetailedOrderSerializer,
) = get_api_classes(
    "serializers.checkout",
    [
        "CheckoutSerializer",
        "OrderLineAttributeSerializer",
        "OrderLineSerializer",
        "OrderSerializer",
        "UserAddressSerializer",
        "OrderRatingPopupSerializer",
        "DetailedOrderSerializer",
    ],
)

__all__ = (
    "CheckoutView",
    "OrderList",
    "OrderDetail",
    "OrderLineList",
    "OrderLineDetail",
    "OrderLineAttributeDetail",
    "UserAddressList",
    "UserAddressDetail",
)



def _with_line_details(queryset):
    """Load what each order line's title, image and options read, in bulk.

    Otherwise every line costs its own product, image and option queries,
    and the order list repeats that for every order on the page.
    """
    return queryset.prefetch_related(
        Prefetch(
            "lines",
            queryset=OrderLine.objects.select_related(
                "product", "product__parent", "service"
            ).prefetch_related(
                "product__images",
                "product__parent__images",
                "attributes__option__option_group__options",
            ),
        )
    )


class OrderList(generics.ListAPIView):
    serializer_class = DetailedOrderSerializer  # Use the detailed serializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        # Start with only the user's orders
        user = self.request.user
        qs = _with_line_details(Order.objects.filter(user=user))

        # Get multiple 'status' query params, e.g. ?status=Pending&status=Finished
        statuses = self.request.query_params.getlist('status')
        if statuses:
            qs = qs.filter(status__in=statuses)

        # Filter by the vendor's business type, e.g. ?business_type=3
        # NOTE: what the app shows as "business_type" is the BusinessCategory
        # (vendor.business_details.business_type.business_category), so we match
        # against business_category_id, not the intermediate BusinessType.
        business_type = self.request.query_params.get('business_type')
        if business_type:
            qs = qs.filter(
                store__vendor__business_details__business_type__business_category_id=business_type
            )

        return qs


class OrderDetail(generics.RetrieveAPIView):
    queryset = _with_line_details(Order.objects.all())
    serializer_class = DetailedOrderSerializer  # Also use the detailed serializer here
    permission_classes = (IsOwner,)


class OrderLineList(generics.ListAPIView):
    queryset = OrderLine.objects.all()
    serializer_class = OrderLineSerializer

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        user = self.request.user
        return super().get_queryset().filter(order_id=pk, order__user=user)


class OrderLineDetail(generics.RetrieveAPIView):
    queryset = OrderLine.objects.all()
    serializer_class = OrderLineSerializer

    def get_queryset(self):
        return super().get_queryset().filter(order__user=self.request.user)


class OrderLineAttributeDetail(generics.RetrieveAPIView):
    queryset = OrderLineAttribute.objects.all()
    serializer_class = OrderLineAttributeSerializer


class CheckoutView(views.APIView):
    """
    Prepare an order for checkout.

    POST(basket, shipping_address,
         [total, shipping_method_code, shipping_charge, billing_address]):
    {
        "basket": "http://testserver/oscarapi/baskets/1/",
        "guest_email": "foo@example.com",
        "total": "100.0",
        "shipping_charge": {
            "currency": "EUR",
            "excl_tax": "10.0",
            "tax": "0.6"
        },
        "shipping_method_code": "no-shipping-required",
        "shipping_address": {
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
        "billing_address": {
            "country": country_url,
            "first_name": "Jos",
            "last_name": "Henken",
            "line1": "Boerderijstraat 19",
            "line2": "",
            "line3": "",
            "line4": "Zwammerdam",
            "notes": "",
            "phone_number": "+31 27 112 9800",
            "postcode": "6666LL",
            "state": "Gerendrecht",
            "title": "Mr"
        }
    }
    returns the order object.
    """
    permission_classes = (IsOwner,)
    order_serializer_class = DetailedOrderSerializer  # Use the detailed serializer here too
    serializer_class = CheckoutSerializer

    # pylint: disable=W0622, W1113
    def post(self, request, format=None, *args, **kwargs):
        basket = parse_basket_from_hyperlink(request.data, format)

        if not request_allows_access_to_basket(request, basket):
            return response.Response(
                "Unauthorized", status=status.HTTP_401_UNAUTHORIZED
            )

        with transaction.atomic():
            # Lock this basket's service slots so a concurrent checkout for the
            # same slot cannot both pass the capacity check (first-checkout-wins).
            lock_service_slots(basket)
            # Then the stockrecords, in that order and never the reverse, so
            # two baskets holding one of each cannot deadlock. Availability is
            # read from what comes back rather than from the lines, which
            # carry figures fetched before the lock was held.
            locked_stock_records = lock_stock_records(basket)
            c_ser = self.serializer_class(
                data=request.data,
                context={
                    "request": request,
                    "locked_stock_records": locked_stock_records,
                },
            )
            if c_ser.is_valid():
                order = c_ser.save()
                # Re-read first: the serializer works on its own instance of
                # this basket and may have written to the row (the
                # unavailable-item policy posted with the checkout), and
                # freeze() saves every field, stale ones included.
                basket.refresh_from_db()
                basket.freeze()
            else:
                return response.Response(c_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)

        o_ser = self.order_serializer_class(order, context={"request": request})
        resp = response.Response(o_ser.data)
        oscarapi_post_checkout.send(
            sender=self,
            order=order,
            user=request.user,
            request=request,
            response=resp,
        )
        return resp


class UserAddressList(generics.ListCreateAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)


class UserAddressDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)

class LastOrderRatingPopupView(generics.RetrieveAPIView):
    serializer_class = OrderRatingPopupSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Define the time window (1 hour)
        time_window = timedelta(hours=1)
        now = timezone.now()

        # Retrieve the most recent order for the user with status "Finished"
        order = Order.objects.filter(
            user=self.request.user,
            status='Finished'  # Filter by status "Finished"
        ).order_by('-date_placed').first()

        if not order:
            return None  # Or raise a 404 error if no orders exist

        # Check if the order is within the 1-hour window and the popup flag is True
        if order.show_rating_popup and (now - order.date_placed) >= time_window:
            # Keep the original state for the response
            response_order = Order.objects.get(pk=order.pk)
            # Update the flag for future requests
            with transaction.atomic():
                order.show_rating_popup = False
                order.save(update_fields=['show_rating_popup'])
            return response_order

        return None  # No popup