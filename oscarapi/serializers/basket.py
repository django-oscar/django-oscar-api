import logging
from decimal import Decimal

from django.utils.translation import ugettext as _
from django.contrib.auth import get_user_model
from rest_framework import serializers

from oscar.core.loading import get_model

from oscarapi.basket import operations
from oscarapi.utils.settings import overridable
from oscarapi.serializers.fields import (
    DrillDownHyperlinkedIdentityField,
    DrillDownHyperlinkedRelatedField,
)
from oscarapi.serializers.utils import (
    OscarModelSerializer,
    OscarHyperlinkedModelSerializer,
)
from oscarapi.serializers.fields import TaxIncludedDecimalField

logger = logging.getLogger(__name__)

User = get_user_model()
Basket = get_model("basket", "Basket")
Line = get_model("basket", "Line")
LineAttribute = get_model("basket", "LineAttribute")
StockRecord = get_model("partner", "StockRecord")
Voucher = get_model("voucher", "Voucher")
Product = get_model("catalogue", "Product")


class VoucherSerializer(OscarModelSerializer):
    class Meta:
        model = Voucher
        fields = overridable(
            "OSCARAPI_VOUCHER_FIELDS",
            default=("name", "code", "start_datetime", "end_datetime"),
        )


class OfferDiscountSerializer(
    serializers.Serializer
):  # pylint: disable=abstract-method
    description = serializers.CharField()
    name = serializers.CharField()
    amount = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="discount"
    )


class VoucherDiscountSerializer(OfferDiscountSerializer):
    voucher = VoucherSerializer(required=False)


class BasketSerializer(serializers.HyperlinkedModelSerializer):
    lines = serializers.HyperlinkedIdentityField(view_name="basket-lines-list")
    offer_discounts = OfferDiscountSerializer(many=True, required=False)
    total_excl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False
    )
    total_excl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False
    )
    total_incl_tax = TaxIncludedDecimalField(
        excl_tax_field="total_excl_tax", decimal_places=2, max_digits=12, required=False
    )
    total_incl_tax_excl_discounts = TaxIncludedDecimalField(
        excl_tax_field="total_excl_tax_excl_discounts",
        decimal_places=2,
        max_digits=12,
        required=False,
    )
    total_tax = TaxIncludedDecimalField(
        excl_tax_value=Decimal("0.00"), decimal_places=2, max_digits=12, required=False
    )
    currency = serializers.CharField(required=False)
    voucher_discounts = VoucherDiscountSerializer(many=True, required=False)
    owner = serializers.HyperlinkedRelatedField(
        view_name="user-detail",
        required=False,
        allow_null=True,
        queryset=User.objects.all(),
    )

    class Meta:
        model = Basket
        fields = overridable(
            "OSCARAPI_BASKET_FIELDS",
            default=(
                "id",
                "owner",
                "status",
                "lines",
                "url",
                "total_excl_tax",
                "total_excl_tax_excl_discounts",
                "total_incl_tax",
                "total_incl_tax_excl_discounts",
                "total_tax",
                "currency",
                "voucher_discounts",
                "offer_discounts",
                "is_tax_known",
            ),
        )


class LineAttributeSerializer(OscarHyperlinkedModelSerializer):
    url = DrillDownHyperlinkedIdentityField(
        view_name="lineattribute-detail",
        extra_url_kwargs={"basket_pk": "line.basket.id", "line_pk": "line.id"},
    )
    line = DrillDownHyperlinkedIdentityField(
        view_name="basket-line-detail", extra_url_kwargs={"basket_pk": "line.basket.id"}
    )

    class Meta:
        model = LineAttribute
        fields = "__all__"


class BasketLineSerializer(OscarHyperlinkedModelSerializer):
    """
    This serializer computes the prices of this line by using the basket
    strategy.
    """

    url = DrillDownHyperlinkedIdentityField(
        view_name="basket-line-detail", extra_url_kwargs={"basket_pk": "basket.id"}
    )
    attributes = LineAttributeSerializer(
        many=True, fields=("url", "option", "value"), required=False, read_only=True
    )
    price_excl_tax = serializers.DecimalField(
        decimal_places=2,
        max_digits=12,
        source="line_price_excl_tax_incl_discounts",
        read_only=True,
    )
    price_incl_tax = TaxIncludedDecimalField(
        decimal_places=2,
        max_digits=12,
        excl_tax_field="line_price_excl_tax_incl_discounts",
        source="line_price_incl_tax_incl_discounts",
        read_only=True,
    )
    price_incl_tax_excl_discounts = TaxIncludedDecimalField(
        decimal_places=2,
        max_digits=12,
        excl_tax_field="line_price_excl_tax",
        source="line_price_incl_tax",
        read_only=True,
    )
    price_excl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="line_price_excl_tax", read_only=True
    )
    warning = serializers.CharField(
        read_only=True, required=False, source="get_warning"
    )

    stockrecord = DrillDownHyperlinkedRelatedField(
        view_name="product-stockrecord-detail",
        extra_url_kwargs={"product_pk": "product_id"},
        queryset=StockRecord.objects.all(),
    )

    class Meta:
        model = Line
        fields = overridable(
            "OSCARAPI_BASKETLINE_FIELDS",
            default=(
                "url",
                "product",
                "quantity",
                "attributes",
                "price_currency",
                "price_excl_tax",
                "price_incl_tax",
                "price_incl_tax_excl_discounts",
                "price_excl_tax_excl_discounts",
                "is_tax_known",
                "warning",
                "basket",
                "stockrecord",
                "date_created",
                "date_updated",
            ),
        )

    def to_representation(self, obj):
        # This override is needed to reflect offer discounts or strategy
        # related prices immediately in the response
        operations.assign_basket_strategy(obj.basket, self.context["request"])

        # Oscar stores the calculated discount in line._discount_incl_tax or
        # line._discount_excl_tax when offers are applied. So by just
        # retrieving the line from the db you will loose this values, that's
        # why we need to get the line from the in-memory resultset here
        lines = (x for x in obj.basket.all_lines() if x.id == obj.id)
        line = next(lines, None)

        return super(BasketLineSerializer, self).to_representation(line)


class VoucherAddSerializer(serializers.Serializer):
    vouchercode = serializers.CharField(max_length=128, required=True)

    def validate(self, attrs):
        # oscar expects this always to be uppercase.
        attrs["vouchercode"] = attrs["vouchercode"].upper()

        request = self.context.get("request")
        try:
            voucher = Voucher.objects.get(code=attrs.get("vouchercode"))

            # check expiry date
            if not voucher.is_active():
                message = _("The '%(code)s' voucher has expired") % {
                    "code": voucher.code
                }
                raise serializers.ValidationError(message)

            # check voucher rules
            is_available, message = voucher.is_available_to_user(request.user)
            if not is_available:
                raise serializers.ValidationError(message)
        except Voucher.DoesNotExist:
            raise serializers.ValidationError(_("Voucher code unknown"))

        # set instance to the voucher so we can use this in the view
        self.instance = voucher
        return attrs

    def create(self, validated_data):
        return Voucher.objects.create(**validated_data)
