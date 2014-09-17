from django.conf import settings
from oscar.core import prices
from oscar.core.loading import get_class, get_model
from rest_framework import serializers

from commerceconnect.utils import OscarHyperlinkedModelSerializer


OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')
ShippingAddress = get_model('order', 'ShippingAddress')
BillingAddress = get_model('order', 'BillingAddress')

class PriceSerializer(serializers.Serializer):
    currency = serializers.CharField(max_length=12, default=settings.OSCAR_DEFAULT_CURRENCY, required=False)
    excl_tax = serializers.DecimalField(decimal_places=2, max_digits=12, default=0, required=True)
    incl_tax = serializers.DecimalField(decimal_places=2, max_digits=12, default=0, required=False)
    tax = serializers.DecimalField(decimal_places=2, max_digits=12, default=0, required=False)

    def restore_object(self, attrs, instance=None):
        print attrs
        if instance is not None:
            instance.currency = attrs.get('currency')
            instance.excl_tax = attrs.get('excl_tax')
            instance.incl_tax = attrs.get('incl_tax')
            instance.tax = attrs.get('tax')
        else:
            instance = prices.Price(
                currency=attrs.get('currency'),
                excl_tax=attrs.get('excl_tax'),
                incl_tax=attrs.get('incl_tax'),
                tax=attrs.get('tax'),
            )

        return instance
        

class ShippingAddressSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = ShippingAddress

class BillingAddressSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = BillingAddress


class OrderSerializer(serializers.Serializer, OrderPlacementMixin):
    basket = serializers.HyperlinkedRelatedField(view_name='basket-detail', required=True)
    total = PriceSerializer(many=False, required=True)
    shipping_method = serializers.CharField(max_length=128, required=True)
    shipping_charge = PriceSerializer(many=False, required=True)
    shipping_adress = ShippingAddressSerializer(many=False, required=False)
    billing_address = BillingAddressSerializer(many=False, required=False)

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            return instance

        basket = attrs.get('basket')
        order_number = self.generate_order_number(basket)
        return self.place_order(
            basket=basket,
            total=attrs.get('total'),
            shipping_method=attrs.get('shipping_method'),
            shipping_charge=attrs.get('shipping_charge'),
            user=self.context.get('user'),
            shipping_adress=attrs.get('shipping_adress'),
            billing_address=attrs.get('billing_address'),
            order_number=order_number,
        )
