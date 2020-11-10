import warnings

from django.db import IntegrityError

from django.conf import settings
from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext as _
from oscar.core import prices
from oscar.core.loading import get_class, get_model
from rest_framework import exceptions, serializers

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


OrderPlacementMixin = get_class("checkout.mixins", "OrderPlacementMixin")
OrderTotalCalculator = get_class("checkout.calculators", "OrderTotalCalculator")
ShippingAddress = get_model("order", "ShippingAddress")
BillingAddress = get_model("order", "BillingAddress")
Order = get_model("order", "Order")
OrderLine = get_model("order", "Line")
OrderLineAttribute = get_model("order", "LineAttribute")
Surcharge = get_model("order", "Surcharge")
StockRecord = get_model("partner", "StockRecord")

Basket = get_model("basket", "Basket")
Country = get_model("address", "Country")
Repository = get_class("shipping.repository", "Repository")

UserAddress = get_model("address", "UserAddress")

VoucherSerializer, OfferDiscountSerializer = get_api_classes(
    "serializers.basket", ["VoucherSerializer", "OfferDiscountSerializer"]
)


class PriceSerializer(serializers.Serializer):
    currency = serializers.CharField(
        max_length=12, default=settings.OSCAR_DEFAULT_CURRENCY, required=False
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


class OrderLineAttributeSerializer(OscarHyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="order-lineattributes-detail")

    class Meta:
        model = OrderLineAttribute
        fields = "__all__"


class OrderLineSerializer(OscarHyperlinkedModelSerializer):
    "This serializer renames some fields so they match up with the basket"

    url = serializers.HyperlinkedIdentityField(view_name="order-lines-detail")
    attributes = OrderLineAttributeSerializer(
        many=True, fields=("url", "option", "value"), required=False
    )
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
                "price_currency",
                "price_excl_tax",
                "price_incl_tax",
                "price_incl_tax_excl_discounts",
                "price_excl_tax_excl_discounts",
                "order",
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
        fields = overridable(
            "OSCARAPI_SURCHARGE_FIELDS",
            default=("name", "code", "incl_tax", "excl_tax"),
        )


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

    def get_offer_discounts(self, obj):
        qs = obj.basket_discounts.filter(offer_id__isnull=False)
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
            warnings.warn(msg)
            return msg

    class Meta:
        model = Order
        fields = overridable(
            "OSCARAPI_ORDER_FIELDS",
            default=(
                "number",
                "basket",
                "url",
                "lines",
                "owner",
                "billing_address",
                "currency",
                "total_incl_tax",
                "total_excl_tax",
                "shipping_incl_tax",
                "shipping_excl_tax",
                "shipping_address",
                "shipping_method",
                "shipping_code",
                "status",
                "email",
                "date_placed",
                "payment_url",
                "offer_discounts",
                "voucher_discounts",
                "surcharges",
            ),
        )


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

    @property
    def request(self):
        return self.context["request"]

    def get_initial_order_status(self, basket):
        return overridable("OSCARAPI_INITIAL_ORDER_STATUS", default="new")

    def validate(self, attrs):
        request = self.request

        if request.user.is_anonymous:
            if not settings.OSCAR_ALLOW_ANON_CHECKOUT:
                message = _("Anonymous checkout forbidden")
                raise serializers.ValidationError(message)

            if not attrs.get("guest_email"):
                # Always require the guest email field if the user is anonymous
                message = _("Guest email is required for anonymous checkouts")
                raise serializers.ValidationError(message)
        else:
            if "guest_email" in attrs:
                # Don't store guest_email field if the user is authenticated
                del attrs["guest_email"]

        basket = attrs.get("basket")
        basket = assign_basket_strategy(basket, request)
        if basket.num_items <= 0:
            message = _("Cannot checkout with empty basket")
            raise serializers.ValidationError(message)

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
        fields = overridable(
            "OSCARAPI_USERADDRESS_FIELDS",
            default=(
                "id",
                "title",
                "first_name",
                "last_name",
                "line1",
                "line2",
                "line3",
                "line4",
                "state",
                "postcode",
                "search_text",
                "phone_number",
                "notes",
                "is_default_for_shipping",
                "is_default_for_billing",
                "country",
                "url",
            ),
        )
