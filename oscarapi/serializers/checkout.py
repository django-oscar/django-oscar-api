import warnings

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from oscar.core import prices
from oscar.core.loading import get_class, get_model
from rest_framework import serializers, exceptions
from django.utils.translation import ugettext_lazy as _

from oscarapi.basket.operations import prepare_basket
from oscarapi.utils import (
    OscarHyperlinkedModelSerializer,
    OscarModelSerializer,
    GetShippingMixin,
)

OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')
ShippingAddress = get_model('order', 'ShippingAddress')
CheckoutSessionData = get_class(
    'checkout.utils', 'CheckoutSessionData')
CheckoutSessionMixin = get_class('checkout.session', 'CheckoutSessionMixin')
BillingAddress = get_model('order', 'BillingAddress')
Order = get_model('order', 'Order')
Basket = get_model('basket', 'Basket')
ShippingMethod = get_model('shipping', 'OrderAndItemCharges')
Country = get_model('address', 'Country')


class PriceSerializer(serializers.Serializer):
    currency = serializers.CharField(
        max_length=12, default=settings.OSCAR_DEFAULT_CURRENCY, required=False)
    excl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=True)
    incl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False)
    tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False)

    def restore_object(self, attrs, instance=None):
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


class CountrySerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Country


class ShippingAddressSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = ShippingAddress


class InlineShippingAddressSerializer(OscarModelSerializer):
    country = serializers.HyperlinkedRelatedField(view_name='country-detail')

    class Meta:
        model = ShippingAddress


class BillingAddressSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = BillingAddress


class InlineBillingAddressSerializer(OscarModelSerializer):
    country = serializers.HyperlinkedRelatedField(view_name='country-detail')

    class Meta:
        model = BillingAddress


class ShippingMethodSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = ShippingMethod
        view_name = 'shippingmethod-detail'


class OrderSerializer(OscarModelSerializer):
    shipping_address = InlineShippingAddressSerializer(
        many=False, required=False)
    billing_address = InlineBillingAddressSerializer(
        many=False, required=False)
    payment_url = serializers.SerializerMethodField('get_payment_url')

    def get_payment_url(self, obj):
        try:
            return reverse('api-payment', args=(obj.pk,))
        except NoReverseMatch:
            msg = "You need to implement a view named 'api-payment' " \
                "which redirects to the payment provider and sets up the " \
                "callbacks."
            warnings.warn(msg)
            return msg

    class Meta:
        model = Order


# TODO: At the moment, only regular shipping charges are possible.
# Most likely CheckoutSerializer should also accept WeightBased shipping
# charges.
class CheckoutSerializer(serializers.Serializer, OrderPlacementMixin,
                         GetShippingMixin):
    basket = serializers.HyperlinkedRelatedField(
        view_name='basket-detail', queryset=Basket.objects)
    total = PriceSerializer(many=False, required=True)
    shipping_method_code = serializers.CharField(
        max_length=128, required=False)
    shipping_charge = PriceSerializer(many=False, required=False)
    shipping_address = ShippingAddressSerializer(many=False, required=False)
    billing_address = BillingAddressSerializer(many=False, required=False)

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
        billing_address = self.get_billing_address(shipping_address) \
            if attrs.get('billing_address', None) is None \
            else attrs.get('billing_address', None)

        if not shipping_method:
            total = attrs.get('total')
            shipping_method = attrs.get('shipping_method', None)
            shipping_charge = attrs.get('shipping_charge', None)
        else:
            shipping_charge = shipping_method.calculate(basket)
            total = self.get_order_totals(
                basket, shipping_charge=shipping_charge)
        if shipping_charge.incl_tax != attrs.get('shipping_charge').incl_tax:
            raise serializers.ValidationError(_('Invalid shipping charge'))
        if total.incl_tax != attrs.get('total').incl_tax:
            raise serializers.ValidationError(_('Invalid order total'))

        attrs['shipping_address'] = shipping_address
        attrs['billing_address'] = billing_address
        attrs['total'] = total
        attrs['shipping_charge'] = shipping_charge
        attrs['shipping_method'] = shipping_method
        attrs['basket'] = basket
        return attrs

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            return instance
        basket = attrs.get('basket')
        order_number = self.generate_order_number(basket)

        try:
            return self.place_order(
                order_number=order_number,
                user=self.request.user,
                basket=basket,
                shipping_address=attrs.get('shipping_address'),
                shipping_method=attrs.get('shipping_method'),
                shipping_charge=attrs.get('shipping_charge'),
                billing_address=attrs.get('billing_address'),
                order_total=attrs.get('total'),
            )
        except ValueError as e:
            raise exceptions.NotAcceptable(e.message)


class TotalChargeSerializer(serializers.Serializer, OrderPlacementMixin):
    basket = serializers.HyperlinkedRelatedField(
        view_name='basket-detail', queryset=Basket.objects)
    shipping_charge = PriceSerializer(many=False, required=True)

    def validate(self, attrs):
        self.request = self.context['request']
        basket = prepare_basket(attrs.get('basket'), self.request)
        if basket.is_empty:
            raise serializers.ValidationError(_('Basket is empty'))
        total = self.get_order_totals(
                basket, shipping_charge=attrs.get('shipping_charge'))

        return {
            'basket_url': self.init_data['basket'],
            'total': PriceSerializer(total).data
        }