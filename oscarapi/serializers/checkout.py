# pylint: disable=W0632, W0223
import warnings
from decimal import Decimal

from django.db import IntegrityError

from django.conf import settings as django_settings
from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext as _
from oscar.core import prices
from oscar.core.loading import get_class, get_model
from rest_framework import exceptions, serializers

from oscarapi import settings
from oscarapi.utils.loading import get_api_classes
from oscarapi.basket.operations import assign_basket_strategy
from oscarapi.utils.settings import overridable
from oscarapi.serializers.utils import (
    OscarHyperlinkedModelSerializer,
    OscarModelSerializer,
)
from oscarapi.serializers.fields import (
    DrillDownHyperlinkedRelatedField,
    TaxIncludedDecimalField,
)
from server.apps.branch.serializers import StoreListSerializer
from oscar.apps.partner.strategy import Selector
from server.apps.basket.constants import (
    UNAVAILABLE_ACTION_CHOICES,
    UNAVAILABLE_ACTION_DEFAULT,
)
from server.apps.partner.availability import ItemsUnavailable, unavailable_lines
from server.apps.vehicle.serializers import VehicleSerializer


OrderPlacementMixin = get_class("checkout.mixins", "OrderPlacementMixin")
OrderTotalCalculator = get_class("checkout.calculators", "OrderTotalCalculator")
ShippingAddress = get_model("order", "ShippingAddress")
BillingAddress = get_model("order", "BillingAddress")
Order = get_model("order", "Order")
OrderLine = get_model("order", "Line")
OrderLineAttribute = get_model("order", "LineAttribute")
Surcharge = get_model("order", "Surcharge")
StockRecord = get_model("partner", "StockRecord")
Vehicle = get_model("vehicle", "Vehicle")

Basket = get_model("basket", "Basket")
Country = get_model("address", "Country")
Repository = get_class("shipping.repository", "Repository")

UserAddress = get_model("address", "UserAddress")

VoucherSerializer, OfferDiscountSerializer = get_api_classes(
    "serializers.basket", ["VoucherSerializer", "OfferDiscountSerializer"]
)


class PriceSerializer(serializers.Serializer):
    currency = serializers.CharField(
        max_length=12, default=django_settings.OSCAR_DEFAULT_CURRENCY, required=False
    )
    excl_tax = serializers.DecimalField(decimal_places=2, max_digits=12, required=True)
    incl_tax = TaxIncludedDecimalField(
        excl_tax_field="excl_tax", decimal_places=2, max_digits=12, required=False
    )
    tax = TaxIncludedDecimalField(
        excl_tax_value="0.00", decimal_places=2, max_digits=12, required=False
    )


class CountrySerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Country
        fields = "__all__"


class ShippingAddressSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = "__all__"


class InlineShippingAddressSerializer(OscarModelSerializer):
    country = serializers.HyperlinkedRelatedField(
        view_name="country-detail", queryset=Country.objects
    )

    class Meta:
        model = ShippingAddress
        fields = "__all__"


class BillingAddressSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = BillingAddress
        fields = "__all__"


class InlineBillingAddressSerializer(OscarModelSerializer):
    country = serializers.HyperlinkedRelatedField(
        view_name="country-detail", queryset=Country.objects
    )

    class Meta:
        model = BillingAddress
        fields = "__all__"


class ShippingMethodSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=128)
    name = serializers.CharField(max_length=128)
    description = serializers.CharField()
    price = serializers.SerializerMethodField("calculate_price")
    is_discounted = serializers.BooleanField()
    discount = serializers.SerializerMethodField("calculate_discount")

    def calculate_discount(self, obj):
        basket = self.context.get("basket")
        return obj.discount(basket)

    def calculate_price(self, obj):
        price = obj.calculate(self.context.get("basket"))
        return PriceSerializer(price).data


def _money(amount):
    """A price as the rest of this payload writes one: "15.00"."""
    return str(Decimal(str(amount or 0)).quantize(Decimal("0.01")))


def _resolve_attribute_option(option, value):
    """The AttributeOption a stored line option value names, or None.

    Values are stored as "ID:<pk>" now and as the display label on older
    lines. Resolved the way ``Basket._get_option_prices`` does it -- id first,
    then the label in any language -- but read from ``option_group.options``
    in memory so a prefetch covers it.
    """
    group = getattr(option, "option_group", None)
    if group is None or value is None:
        return None
    candidates = list(group.options.all())

    raw = value
    if isinstance(raw, dict):
        raw = raw.get("id") or raw.get("pk")
    if isinstance(raw, str):
        raw = raw.strip()
        if raw.upper().startswith("ID:"):
            raw = raw.split(":", 1)[1].strip()
        if raw.isdigit():
            raw = int(raw)
    if isinstance(raw, int):
        for candidate in candidates:
            if candidate.pk == raw:
                return candidate

    label = str(value).strip().lower()
    if not label:
        return None
    fields = ["option"] + [
        "option_%s" % code for code, __ in getattr(django_settings, "LANGUAGES", [])
    ]
    for candidate in sorted(candidates, key=lambda c: c.pk):
        for field in fields:
            text = getattr(candidate, field, None)
            if text and text.strip().lower() == label:
                return candidate
    return None


class OrderLineAttributeSerializer(OscarHyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="order-lineattributes-detail")

    class Meta:
        model = OrderLineAttribute
        fields = ["url", "option", "value"]


class OrderLineSerializer(OscarHyperlinkedModelSerializer):
    "This serializer renames some fields so they match up with the basket"

    url = serializers.HyperlinkedIdentityField(view_name="order-lines-detail")
    attributes = OrderLineAttributeSerializer(many=True, required=False)
    price_currency = serializers.CharField(source="order.currency", max_length=12)
    price_excl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="line_price_excl_tax"
    )
    price_incl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="line_price_incl_tax"
    )
    price_incl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="line_price_before_discounts_incl_tax"
    )
    price_excl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="line_price_before_discounts_excl_tax"
    )
    stockrecord = DrillDownHyperlinkedRelatedField(
        view_name="product-stockrecord-detail",
        extra_url_kwargs={"product_pk": "product_id"},
        queryset=StockRecord.objects.all(),
    )
    service_id = serializers.IntegerField(source="service.id", read_only=True, default=None, allow_null=True)
    service_start_at = serializers.DateTimeField(read_only=True, default=None, allow_null=True)

    # Enough to draw the line without a second source. The app used to take
    # its item list from ``basket.products`` for want of these -- and the
    # basket is frozen at checkout, so a line the vendor later removed kept
    # showing there as an ordinary item inside the old total.
    product_id = serializers.IntegerField(read_only=True, allow_null=True)
    product_title = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()

    # Priced options (size, extras). ``price_*`` above is the product alone:
    # the basket adds options on top at checkout, into the order total and
    # onto no line. Without these the lines of an order with a priced option
    # add up to less than ``total_incl_tax`` and nothing says why.
    options = serializers.SerializerMethodField()
    options_price = serializers.SerializerMethodField()
    total_incl_tax = serializers.SerializerMethodField()
    total_excl_tax = serializers.SerializerMethodField()

    def get_product_title(self, obj):
        # The product's title follows the request language; the line's own
        # is a snapshot in whatever language the order was placed in.
        if obj.product is not None:
            return obj.product.get_title()
        return obj.title

    def get_product_image(self, obj):
        if obj.product is None:
            return None
        for image in obj.product.get_all_images():
            if getattr(image, "original", None):
                return image.original.url
        return None

    def get_options(self, obj):
        options = []
        for attribute in obj.attributes.all():
            option = attribute.option
            raw = attribute.value
            for value in raw if isinstance(raw, (list, tuple)) else [raw]:
                chosen = _resolve_attribute_option(option, value)
                if chosen is None and str(value).strip().upper().startswith("ID:"):
                    # The option it pointed at has since been deleted. A bare
                    # "ID:31" means nothing to the customer, and its price is
                    # gone with it.
                    continue
                options.append(
                    {
                        # The option's code is all that is left once a vendor
                        # deletes the option itself.
                        "name": option.name if option else attribute.type,
                        "value": chosen.option if chosen else str(value),
                        "value_id": chosen.id if chosen else None,
                        # Per unit, as on the product screen.
                        # ``options_price`` is the line's whole share.
                        "price": _money(chosen.price if chosen else 0),
                    }
                )
        return options

    def _options_price(self, obj):
        # Priced by the basket's own method, the one that built the order
        # total, so the line totals here cannot drift from it.
        if not hasattr(obj, "_options_price_cache"):
            obj._options_price_cache = Basket()._get_option_prices(obj)
        return obj._options_price_cache

    def get_options_price(self, obj):
        return _money(self._options_price(obj))

    def get_total_incl_tax(self, obj):
        return _money((obj.line_price_incl_tax or 0) + self._options_price(obj))

    def get_total_excl_tax(self, obj):
        # The basket adds option prices to the excl-tax total unchanged too.
        return _money((obj.line_price_excl_tax or 0) + self._options_price(obj))

    class Meta:
        model = OrderLine
        fields = overridable(
            "OSCARAPI_ORDERLINE_FIELDS",
            default=(
                "attributes",
                "url",
                "product",
                "stockrecord",
                "quantity",
                "note",
                "price_currency",
                "price_excl_tax",
                "price_incl_tax",
                "price_incl_tax_excl_discounts",
                "price_excl_tax_excl_discounts",
                "order",
                "service_id",
                "service_start_at",
            ),
        )


class OrderOfferDiscountSerializer(OfferDiscountSerializer):
    name = serializers.CharField(source="offer_name")
    amount = serializers.DecimalField(decimal_places=2, max_digits=12)


class OrderVoucherOfferSerializer(OrderOfferDiscountSerializer):
    voucher = VoucherSerializer(required=False)


class InlineSurchargeSerializer(OscarModelSerializer):
    class Meta:
        model = Surcharge
        fields = settings.SURCHARGE_FIELDS


class OrderSerializer(OscarHyperlinkedModelSerializer):
    """
    The order serializer tries to have the same kind of structure as the
    basket. That way the same kind of logic can be used to display the order
    as the basket in the checkout process.
    """

    owner = serializers.HyperlinkedRelatedField(
        view_name="user-detail", read_only=True, source="user"
    )
    lines = serializers.HyperlinkedIdentityField(view_name="order-lines-list")
    shipping_address = InlineShippingAddressSerializer(many=False, required=False)
    billing_address = InlineBillingAddressSerializer(many=False, required=False)

    email = serializers.EmailField(read_only=True)

    payment_url = serializers.SerializerMethodField()
    offer_discounts = serializers.SerializerMethodField()
    voucher_discounts = serializers.SerializerMethodField()
    surcharges = InlineSurchargeSerializer(many=True, required=False)

    branch = serializers.SerializerMethodField()

    def get_branch(self, obj):
        """Fetch store details and return them as 'branch'"""
        if obj.store:
            return StoreListSerializer(obj.store).data
        return None


    def get_offer_discounts(self, obj):
        qs = obj.basket_discounts.filter(
            offer_id__isnull=False, voucher_id__isnull=True
        )
        return OrderOfferDiscountSerializer(qs, many=True).data

    def get_voucher_discounts(self, obj):
        qs = obj.basket_discounts.filter(voucher_id__isnull=False)
        return OrderVoucherOfferSerializer(qs, many=True).data

    def get_payment_url(self, obj):
        try:
            return reverse("api-payment", args=(obj.pk,))
        except NoReverseMatch:
            msg = (
                "You need to implement a view named 'api-payment' "
                "which redirects to the payment provider and sets up the "
                "callbacks."
            )
            warnings.warn(msg, stacklevel=2)
            return msg

    class Meta:
        model = Order
        fields = settings.ORDER_FIELDS + ("branch",)


class CheckoutSerializer(serializers.Serializer, OrderPlacementMixin):
    basket = serializers.HyperlinkedRelatedField(
        view_name="basket-detail", queryset=Basket.objects
    )
    guest_email = serializers.EmailField(allow_blank=True, required=False)
    total = serializers.DecimalField(decimal_places=2, max_digits=12, required=False)
    shipping_method_code = serializers.CharField(max_length=128, required=False)
    shipping_charge = PriceSerializer(many=False, required=False)
    shipping_address = ShippingAddressSerializer(many=False, required=False)
    billing_address = BillingAddressSerializer(many=False, required=False)

    vehicle = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),  # You probably want to filter to only user’s vehicles
        required=False,
        allow_null=True
    )

    # What to do if the vendor cannot supply part of this order. Optional:
    # absent means whatever the review screen already saved on the basket.
    unavailable_item_action = serializers.ChoiceField(
        choices=UNAVAILABLE_ACTION_CHOICES, required=False
    )

    @property
    def request(self):
        return self.context["request"]

    # pylint: disable=W0613
    def get_initial_order_status(self, basket):
        return settings.INITIAL_ORDER_STATUS

    def validate(self, attrs):
        request = self.request

        if request.user.is_anonymous:
            if not django_settings.OSCAR_ALLOW_ANON_CHECKOUT:
                message = _("Anonymous checkout forbidden")
                raise serializers.ValidationError(message)

            # if not attrs.get("guest_email"):
            #     # Always require the guest email field if the user is anonymous
            #     message = _("Guest email is required for anonymous checkouts")
            #     raise serializers.ValidationError(message)
        # else:
        #     if "guest_email" in attrs:
        #         # Don't store guest_email field if the user is authenticated
        #         del attrs["guest_email"]

        basket = attrs.get("basket")
        basket = assign_basket_strategy(basket, request)
        if basket.num_items <= 0:
            message = _("Cannot checkout with empty basket")
            raise serializers.ValidationError(message)

        # Stock moves between adding to the basket and tapping checkout, so
        # this read is the authoritative one -- the review screen's is
        # advisory. The customer is on the screen here, so we block and name
        # what is short rather than applying their unavailable-item policy:
        # that policy is a standing instruction for the moment they are gone,
        # and silently dropping a line in front of them would be worse than
        # saying so. See server/apps/partner/availability.py.
        short_lines = unavailable_lines(
            basket.all_lines(), self.context.get("locked_stock_records")
        )
        if short_lines:
            raise ItemsUnavailable(short_lines)

        from server.apps.service.models import Service

        service_messages = []
        for line in basket.all_lines():
            if line.product and line.product.service.exists():
                if not line.service_id:
                    service_messages.append(
                        _("'%(title)s' requires a service time slot to complete checkout.")
                        % {"title": line.product.get_title()}
                    )
                else:
                    try:
                        service_obj = Service.objects.get(id=line.service_id)
                    except Service.DoesNotExist:
                        service_messages.append(
                            _("'%(title)s' has an invalid service selection.")
                            % {"title": line.product.get_title()}
                        )
                        continue
                    if not line.service_start_at:
                        service_messages.append(
                            _("'%(title)s' requires a service start time to complete checkout.")
                            % {"title": line.product.get_title()}
                        )
                        continue
                    try:
                        service_obj.validate_booking(line.service_start_at)
                    except ValueError as exc:
                        service_messages.append(
                            _("'%(title)s': %(error)s")
                            % {"title": line.product.get_title(), "error": str(exc)}
                        )
                        continue
                    booked_count = service_obj.get_booked_count_for_slot(
                        line.service_start_at
                    )
                    if booked_count + line.quantity > service_obj.max_services_per_slot:
                        service_messages.append(
                            _("'%(title)s' time slot is fully booked. Please select a different time.")
                            % {"title": line.product.get_title()}
                        )
        if service_messages:
            raise serializers.ValidationError({"service_slots": service_messages})

        shipping_method = self._shipping_method(
            request,
            basket,
            attrs.get("shipping_method_code"),
            attrs.get("shipping_address"),
        )
        shipping_charge = shipping_method.calculate(basket)
        posted_shipping_charge = attrs.get("shipping_charge")

        if posted_shipping_charge is not None:
            posted_shipping_charge = prices.Price(**posted_shipping_charge)
            # test submitted data.
            if not posted_shipping_charge == shipping_charge:
                message = _(
                    "Shipping price incorrect %s != %s"
                    % (posted_shipping_charge, shipping_charge)
                )
                raise serializers.ValidationError(message)

        posted_total = attrs.get("total")
        total = OrderTotalCalculator().calculate(basket, shipping_charge)
        if posted_total is not None:
            if posted_total != total.incl_tax:
                message = _("Total incorrect %s != %s" % (posted_total, total.incl_tax))
                raise serializers.ValidationError(message)

        vehicle = attrs.get('vehicle')
        if vehicle and vehicle.customer.user.id != request.user.id:
            raise serializers.ValidationError("You cannot use a vehicle that does not belong to you.")


        # update attrs with validated data.
        attrs["order_total"] = total
        attrs["shipping_method"] = shipping_method
        attrs["shipping_charge"] = shipping_charge
        attrs["basket"] = basket
        return attrs

    def create(self, validated_data):
        try:
            basket = validated_data.get("basket")
            order_number = self.generate_order_number(basket)
            request = self.request
            vehicle = validated_data.pop('vehicle', None)

            # Precedence is body, then basket, then default. Persisting the
            # posted value first keeps the basket and the order agreeing;
            # passing it on explicitly is what OrderCreator's setdefault
            # expects, so the body still wins if the save is a no-op.
            unavailable_item_action = validated_data.get("unavailable_item_action")
            if unavailable_item_action:
                if basket.unavailable_item_action != unavailable_item_action:
                    basket.unavailable_item_action = unavailable_item_action
                    basket.save(update_fields=["unavailable_item_action"])
            else:
                unavailable_item_action = (
                    basket.unavailable_item_action or UNAVAILABLE_ACTION_DEFAULT
                )

            if "shipping_address" in validated_data:
                shipping_address = ShippingAddress(**validated_data["shipping_address"])
            else:
                shipping_address = None

            if "billing_address" in validated_data:
                billing_address = BillingAddress(**validated_data["billing_address"])
            else:
                billing_address = None

            return self.place_order(
                order_number=order_number,
                user=request.user,
                basket=basket,
                shipping_address=shipping_address,
                shipping_method=validated_data.get("shipping_method"),
                shipping_charge=validated_data.get("shipping_charge"),
                billing_address=billing_address,
                order_total=validated_data.get("order_total"),
                guest_email=validated_data.get("guest_email") or "",
                vehicle=vehicle,
                unavailable_item_action=unavailable_item_action,
            )
        except ValueError as e:
            raise exceptions.NotAcceptable(str(e))

    def _shipping_method(self, request, basket, shipping_method_code, shipping_address):
        repo = Repository()

        default = repo.get_default_shipping_method(
            basket=basket,
            user=request.user,
            request=request,
            shipping_addr=shipping_address,
        )

        if shipping_method_code is not None:
            methods = repo.get_shipping_methods(
                basket=basket,
                user=request.user,
                request=request,
                shipping_addr=shipping_address,
            )

            find_method = (s for s in methods if s.code == shipping_method_code)
            shipping_method = next(find_method, default)
            return shipping_method

        return default


class UserAddressSerializer(OscarModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="useraddress-detail")
    country = serializers.HyperlinkedRelatedField(
        view_name="country-detail", queryset=Country.objects
    )

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["user"] = request.user
        try:
            return super(UserAddressSerializer, self).create(validated_data)
        except IntegrityError as e:
            raise exceptions.NotAcceptable(str(e))

    def update(self, instance, validated_data):
        # to be sure that we cannot change the owner of an address. If you
        # want this, please override the serializer
        request = self.context["request"]
        validated_data["user"] = request.user
        try:
            return super(UserAddressSerializer, self).update(instance, validated_data)
        except IntegrityError as e:
            raise exceptions.NotAcceptable(str(e))

    class Meta:
        model = UserAddress
        fields = settings.USERADDRESS_FIELDS

class OrderNotificationLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.title")
    quantity = serializers.IntegerField()
    price_excl_tax = serializers.SerializerMethodField()
    price_incl_tax = serializers.SerializerMethodField()

    def get_price_excl_tax(self, obj):
        return float(obj.line_price_excl_tax)  # Convert Decimal to float

    def get_price_incl_tax(self, obj):
        return float(obj.line_price_incl_tax)  # Convert Decimal to float

    class Meta:
        model = OrderLine
        fields = ["product_name", "quantity", "price_excl_tax", "price_incl_tax"]

class OrderNotificationSerializer(serializers.ModelSerializer):
    """Serializer for WebSocket order notifications (for Celery)"""
    order_number = serializers.CharField(source="number")
    total_excl_tax = serializers.SerializerMethodField()
    total_incl_tax = serializers.SerializerMethodField()
    status = serializers.CharField()
    email = serializers.EmailField()
    date_placed = serializers.DateTimeField()
    lines = OrderNotificationLineSerializer(many=True, source="lines.all")
    branch = serializers.SerializerMethodField()
    basket = serializers.SerializerMethodField()

    def get_total_excl_tax(self, obj):
        return float(obj.total_excl_tax)

    def get_total_incl_tax(self, obj):
        return float(obj.total_incl_tax)
    
    def get_basket(self, obj):
        if obj.basket:
            basket = obj.basket
            basket.strategy = Selector().strategy()
            return self._serialize_basket(basket)
        return None
    
    def _serialize_basket(self, basket):
        return {
            "id": basket.id,
            "total_excl_tax": float(basket.total_excl_tax),  # Convert
            "total_excl_tax_excl_discounts": float(basket.total_excl_tax_excl_discounts),
            "total_incl_tax": float(basket.total_incl_tax),
            "total_incl_tax_excl_discounts": float(basket.total_incl_tax_excl_discounts),
            "total_tax": float(basket.total_tax),  # Convert
            "currency": basket.currency,
            "vendor": self._get_vendor(basket),
            "branch": self._get_branch(basket),
            "products_in_basket": self._get_products_in_basket(basket),
        }


    def _get_vendor(self, basket):
        """Get vendor details"""
        if basket.branch and basket.branch.vendor:
            return {
                "id": basket.branch.vendor.id,
                "name": basket.branch.vendor.name,
            }
        return None
    
    def _get_branch(self, basket):
        """Get branch details"""
        if basket.branch:
            return {
                "id": basket.branch.id,
                "name": basket.branch.name,
                "latitude": basket.branch.location.y,
                "longitude": basket.branch.location.x,
            }
        return None
    
    def _get_products_in_basket(self, basket):
        products_data = {}
        for line in basket.lines.all():
            line_data = {
                "qty": line.quantity,
                "line_id": line.id,
                "attributes": self._get_attributes(line),
                "title": line.product.title,
                "original_price": float(line.product.original_price),  # Convert
                "price_currency": line.product.price_currency,
                "selling_price": float(line.product.selling_price),  # Convert
                "image": self._get_product_images(line.product),
            }
            products_data[str(line.product.id)] = [line_data]
        return products_data

    def _get_product_images(self, product):
        """Get product images"""
        images = [image.original.url for image in product.get_all_images()]
        return images[0] if images else ""

    def _get_attributes(self, line):
        """Get line attributes"""
        return [{"value": attr.value, "name": attr.option.name} for attr in line.attributes.all()]
    

    def get_branch(self, obj):
        """Fetch store details and return them as 'branch'"""
        if obj.store:
            return StoreListSerializer(obj.store).data
        return None

    

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "total_excl_tax",
            "total_incl_tax",
            "status",
            "email",
            "date_placed",
            "currency",
            "lines",
            "branch",
            "basket"
        ]



class OrderRatingPopupSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    vendor_name = serializers.CharField(source='store.vendor.name', read_only=True)
    vendor_banner = serializers.ImageField(source='store.vendor.banner', read_only=True)
    vendor_logo = serializers.ImageField(source='store.vendor.business_details.logo', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 
            'number', 
            'show_rating_popup', 
            'store', 
            'store_name',
            'vendor_name',
            'vendor_banner',
            'vendor_logo'
        ]
        read_only_fields = ['id', 'number', 'store', 'store_name', 'vendor_name', 'vendor_banner', 'vendor_logo']


# Create a custom serializer that includes detailed basket and product information
class DetailedOrderSerializer(OrderSerializer):
    """
    Extended OrderSerializer that includes detailed basket and product information
    instead of just URLs.
    """
    vehicle = VehicleSerializer(read_only=True)
    timeline = serializers.SerializerMethodField()
    order_rating = serializers.SerializerMethodField()
    class Meta(OrderSerializer.Meta):
        model = Order
        fields = OrderSerializer.Meta.fields + ("vehicle", "timeline", "order_rating")
    
    def to_representation(self, instance):
        # Get the standard representation
        representation = super().to_representation(instance)
        
        # Add detailed lines information instead of just URL
        order_lines = instance.lines.all()
        representation['lines'] = OrderLineSerializer(
            order_lines, 
            many=True, 
            context=self.context
        ).data
        
        # Add basket details if available
        if instance.basket:
            basket = instance.basket
            # Ensure the basket has a strategy for price calculations
            basket.strategy = Selector().strategy()
            
            representation['basket'] = {
                "id": basket.id,
                "total_excl_tax": float(basket.total_excl_tax),
                "total_excl_tax_excl_discounts": float(basket.total_excl_tax_excl_discounts),
                "total_incl_tax": float(basket.total_incl_tax),
                "total_incl_tax_excl_discounts": float(basket.total_incl_tax_excl_discounts),
                "total_tax": float(basket.total_tax),
                "currency": basket.currency,
                "note": getattr(basket, "note", None),
                "products": self._get_products_in_basket(basket),
            }
        
        return representation
    
    def _get_products_in_basket(self, basket):
        """Get detailed product information from the basket"""
        products_data = []
        for line in basket.lines.all():
            # Get product images
            images = []
            if hasattr(line.product, 'get_all_images'):
                images = [image.original.url for image in line.product.get_all_images() if hasattr(image, 'original')]
            
            # Get line attributes
            attributes = []
            for attr in line.attributes.all():
                attributes.append({
                    "value": attr.value,
                    "name": attr.option.name if hasattr(attr.option, 'name') else str(attr.option)
                })
            
            line_data = {
                "id": line.id,
                "product_id": line.product.id,
                "title": line.product.get_title(),
                "quantity": line.quantity,
                "attributes": attributes,
                "price_excl_tax": float(line.line_price_excl_tax),
                "price_incl_tax": float(line.line_price_incl_tax),
                "price_currency": basket.currency,
                "images": images[0] if images else None,
            }
            products_data.append(line_data)
        
        return products_data

    def get_timeline(self, obj):
        from server.apps.order.serializers import OrderTimelineEventSerializer

        timeline_events = obj.timeline_events.all().order_by('-date_created')
        return OrderTimelineEventSerializer(timeline_events, many=True).data

    def get_order_rating(self, obj):
        from oscar.core.loading import get_model
        StoreRating = get_model('stores', 'StoreRating')
        order_rating = StoreRating.objects.filter(order=obj).first()
        return order_rating.rating if order_rating else None

# # Create a custom serializer that includes detailed basket and product information
# class DetailedOrderSerializer(OrderSerializer):
#     """
#     Extended OrderSerializer that includes detailed basket and product information
#     instead of just URLs.
#     """
    
#     class Meta(OrderSerializer.Meta):
#         model = Order
#         fields = OrderSerializer.Meta.fields
    
#     def to_representation(self, instance):
#         # Get the standard representation
#         representation = super().to_representation(instance)
        
#         # Add detailed lines information instead of just URL
#         order_lines = instance.lines.all()
#         representation['lines'] = OrderLineSerializer(
#             order_lines, 
#             many=True, 
#             context=self.context
#         ).data
        
#         # Add basket details if available
#         if instance.basket:
#             basket = instance.basket
#             # Ensure the basket has a strategy for price calculations
#             basket.strategy = Selector().strategy()
            
#             representation['basket'] = {
#                 "id": basket.id,
#                 "total_excl_tax": float(basket.total_excl_tax),
#                 "total_excl_tax_excl_discounts": float(basket.total_excl_tax_excl_discounts),
#                 "total_incl_tax": float(basket.total_incl_tax),
#                 "total_incl_tax_excl_discounts": float(basket.total_incl_tax_excl_discounts),
#                 "total_tax": float(basket.total_tax),
#                 "currency": basket.currency,
#                 "products": self._get_products_in_basket(basket),
#             }
        
#         return representation
    
#     def _get_products_in_basket(self, basket):
#         """Get detailed product information from the basket"""
#         products_data = []
#         for line in basket.lines.all():
#             # Get product images
#             images = []
#             if hasattr(line.product, 'get_all_images'):
#                 images = [image.original.url for image in line.product.get_all_images() if hasattr(image, 'original')]
            
#             # Get line attributes
#             attributes = []
#             for attr in line.attributes.all():
#                 attributes.append({
#                     "value": attr.value,
#                     "name": attr.option.name if hasattr(attr.option, 'name') else str(attr.option)
#                 })
            
#             line_data = {
#                 "id": line.id,
#                 "product_id": line.product.id,
#                 "title": line.product.get_title(),
#                 "quantity": line.quantity,
#                 "attributes": attributes,
#                 "price_excl_tax": float(line.line_price_excl_tax),
#                 "price_incl_tax": float(line.line_price_incl_tax),
#                 "price_currency": basket.currency,
#                 "images": images[0] if images else None,
#             }
#             products_data.append(line_data)
        
#         return products_data

