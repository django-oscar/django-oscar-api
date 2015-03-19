from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from oscar.core.loading import get_class, get_model
from oscarapi.basket.operations import prepare_basket
from oscarapi.utils import GetShippingMixin
from oscarapi.serializers import ShippingAddressSerializer, PriceSerializer


CheckoutSessionMixin = get_class('checkout.session', 'CheckoutSessionMixin')
Basket = get_model('basket', 'Basket')
Repository = get_class('shipping.repository', 'Repository')
NoShippingRequired = get_class('shipping.methods', 'NoShippingRequired')


class ShippingSerializer(serializers.Serializer, CheckoutSessionMixin, GetShippingMixin):
    basket = serializers.HyperlinkedRelatedField(
        view_name='basket-detail', queryset=Basket.objects)
    shipping_address = ShippingAddressSerializer(many=False, required=True)
    shipping_method_code = serializers.CharField(max_length=128, required=False)

    def validate(self, attrs):
        self.request = self.context['request']
        basket = prepare_basket(attrs.get('basket'), self.request)
        if basket.is_empty:
            raise serializers.ValidationError(_('Basket is empty'))
        self._set_new_address(basket, attrs.get('shipping_address'))
        shipping_address = self.get_shipping_address(basket)
        shipping_method = self.get_shipping_method(
            basket, shipping_address)
        if shipping_method is None:
            shipping_method = self._shipping_method(
                self.request, basket,
                attrs.get('shipping_method_code'),
                shipping_address
            )
        shipping_charge = shipping_method.calculate(basket)
        return {
            'basket_url': self.init_data['basket'],
            'shipping_address': ShippingAddressSerializer(shipping_address, context={'request': self.request}).data,
            'shipping_method_code': shipping_method.code,
            'shipping_charge': PriceSerializer(shipping_charge).data
        }