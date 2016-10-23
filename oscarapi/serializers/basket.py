import logging
from rest_framework import serializers

from oscarapi.utils import (
    overridable,
    OscarModelSerializer,
    OscarHyperlinkedModelSerializer,
    DrillDownHyperlinkedIdentityField
)
from oscarapi.serializers.fields import TaxIncludedDecimalField

from django.utils.translation import ugettext as _
from oscar.core.loading import get_model
from decimal import Decimal

logger = logging.getLogger(__name__)

Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')
LineAttribute = get_model('basket', 'LineAttribute')
StockRecord = get_model('partner', 'StockRecord')
Voucher = get_model('voucher', 'Voucher')


class VoucherSerializer(OscarModelSerializer):
    class Meta:
        model = Voucher
        fields = overridable('OSCARAPI_VOUCHER_FIELDS', default=(
            'name', 'code', 'start_datetime', 'end_datetime'
        ))


class OfferDiscountSerializer(serializers.Serializer):
    description = serializers.CharField()
    name = serializers.CharField()
    amount = serializers.DecimalField(
        decimal_places=2, max_digits=12, source='discount')


class VoucherDiscountSerializer(OfferDiscountSerializer):
    voucher = VoucherSerializer(required=False)


class BasketSerializer(serializers.HyperlinkedModelSerializer):
    lines = serializers.HyperlinkedIdentityField(view_name='basket-lines-list')
    offer_discounts = OfferDiscountSerializer(many=True, required=False)
    total_excl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False)
    total_excl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False)
    total_incl_tax = TaxIncludedDecimalField(
        excl_tax_field='total_excl_tax', decimal_places=2,
        max_digits=12, required=False)
    total_incl_tax_excl_discounts = TaxIncludedDecimalField(
        excl_tax_field='total_excl_tax_excl_discounts', decimal_places=2,
        max_digits=12, required=False)
    total_tax = TaxIncludedDecimalField(
        excl_tax_value=Decimal('0.00'), decimal_places=2,
        max_digits=12, required=False)
    currency = serializers.CharField(required=False)
    voucher_discounts = VoucherDiscountSerializer(many=True, required=False)

    class Meta:
        model = Basket
        fields = overridable('OSCARAPI_BASKET_FIELDS', default=(
            'id', 'owner', 'status', 'lines',
            'url', 'total_excl_tax',
            'total_excl_tax_excl_discounts', 'total_incl_tax',
            'total_incl_tax_excl_discounts', 'total_tax', 'currency',
            'voucher_discounts', 'offer_discounts', 'is_tax_known'))

    def get_validation_exclusions(self, instance=None):
        """
        This is needed because oscar declared the owner field as ``null=True``,
        but ``blank=False``. That means the validator will claim you can not
        leave this value set to None.
        """
        return super(BasketSerializer, self).get_validation_exclusions(
            instance) + ['owner']


class LineAttributeSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = LineAttribute
        fields = '__all__'


class BasketLineSerializer(OscarHyperlinkedModelSerializer):
    """
    This serializer computes the prices of this line by using the basket
    strategy.
    """
    url = DrillDownHyperlinkedIdentityField(
        view_name='basket-line-detail',
        extra_url_kwargs={'basket_pk': 'basket.id'})
    attributes = LineAttributeSerializer(
        many=True, fields=('url', 'option', 'value'),
        required=False, read_only=True)
    price_excl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12,
        source='line_price_excl_tax_incl_discounts')
    price_incl_tax = TaxIncludedDecimalField(
        decimal_places=2, max_digits=12,
        excl_tax_field='line_price_excl_tax_incl_discounts',
        source='line_price_incl_tax_incl_discounts')
    price_incl_tax_excl_discounts = TaxIncludedDecimalField(
        decimal_places=2, max_digits=12,
        excl_tax_field='line_price_excl_tax',
        source='line_price_incl_tax')
    price_excl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12,
        source='line_price_excl_tax')
    warning = serializers.CharField(
        read_only=True, required=False, source='get_warning')

    @property
    def basket_pk(self):
        return self.kwargs.get('basket_pk')

    class Meta:
        model = Line
        fields = overridable('OSCARAPI_BASKETLINE_FIELDS', default=(
            'url', 'product', 'quantity', 'attributes', 'price_currency',
            'price_excl_tax', 'price_incl_tax',
            'price_incl_tax_excl_discounts', 'price_excl_tax_excl_discounts',
            'is_tax_known', 'warning', 'basket', 'stockrecord', 'date_created'
        ))


class LineSerializer(serializers.HyperlinkedModelSerializer):
    """
    This serializer just shows fields stored in the database for this line.
    """
    attributes = LineAttributeSerializer(
        many=True,
        fields=('url', 'option', 'value'),
        required=False,
        read_only=True)

    class Meta:
        model = Line
        fields = '__all__'


class StockRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = StockRecord


class VoucherAddSerializer(serializers.Serializer):
    vouchercode = serializers.CharField(max_length=128, required=True)

    def validate(self, attrs):
        # oscar expects this always to be uppercase.
        attrs['vouchercode'] = attrs['vouchercode'].upper()

        request = self.context.get('request')
        try:
            voucher = Voucher.objects.get(code=attrs.get('vouchercode'))

            # check expiry date
            if not voucher.is_active():
                message = _("The '%(code)s' voucher has expired") % {
                    'code': voucher.code
                }
                raise serializers.ValidationError(message)

            # check voucher rules
            is_available, message = voucher.is_available_to_user(request.user)
            if not is_available:
                raise serializers.ValidationError(message)
        except Voucher.DoesNotExist:
            raise serializers.ValidationError(_('Voucher code unknown'))

        # set instance to the voucher so we can use this in the view
        self.instance = voucher
        return attrs

    def create(self, validated_data):
        return Voucher.objects.create(**validated_data)
