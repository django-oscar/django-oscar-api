from rest_framework import serializers

from commerceconnect.utils import overridable, OscarModelSerializer
from oscar.core.loading import get_model


Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')
LineAttribute = get_model('basket', 'LineAttribute')
StockRecord = get_model('partner', 'StockRecord')
Option = get_model('catalogue', 'Option')


class BasketSerializer(serializers.HyperlinkedModelSerializer):
    lines = serializers.HyperlinkedIdentityField(view_name='basket-lines-list')
    offer_applications = serializers.SerializerMethodField(
        'get_offer_applications')
    total_excl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=True)
    total_excl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=True)
    total_incl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=True)
    total_incl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=True)
    total_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=True)
    voucher_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=True)

    class Meta:
        model = Basket
        fields = overridable('CC_BASKET_FIELDS', default=[
            'id', 'owner', 'status', 'vouchers', 'lines',
            'url', 'offer_applications', 'total_excl_tax',
            'total_excl_tax_excl_discounts', 'total_incl_tax',
            'total_incl_tax_excl_discounts', 'total_tax', 'voucher_discounts'])

    def get_validation_exclusions(self, instance=None):
        """
        This is needed because oscar declared the owner field as ``null=True``,
        but ``blank=False``. That means the validator will claim you can not
        leave this value set to None.
        """
        return super(BasketSerializer, self).get_validation_exclusions(
            instance) + ['owner']

    def get_offer_applications(self, obj):
        if hasattr(obj, 'offer_applications'):
            return obj.offer_applications.offers
        return {}


class LineAttributeSerializer(serializers.HyperlinkedModelSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(LineAttributeSerializer, self).__init__(*args, **kwargs)
        if fields:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    class Meta:
        model = LineAttribute


class LineSerializer(serializers.HyperlinkedModelSerializer):
    attributes = LineAttributeSerializer(
        many=True, fields=('url', 'option', 'value'), required=False)

    class Meta:
        model = Line


class OptionSerializer(OscarModelSerializer):

    class Meta:
        model = Option


class StockRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = StockRecord
