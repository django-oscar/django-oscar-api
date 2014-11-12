import warnings

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from oscar.core import prices
from oscar.core.loading import get_class, get_model
from rest_framework import serializers, exceptions

from commerceconnect.apps.basket.utils import prepare_basket
from commerceconnect.utils import (
    OscarHyperlinkedModelSerializer,
    OscarModelSerializer
)


OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')
ShippingAddress = get_model('order', 'ShippingAddress')
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
class CheckoutSerializer(serializers.Serializer, OrderPlacementMixin):
    basket = serializers.HyperlinkedRelatedField(
        view_name='basket-detail', queryset=Basket.editable)
    total = PriceSerializer(many=False, required=True)
    shipping_method = serializers.HyperlinkedRelatedField(
        view_name='shippingmethod-detail', queryset=ShippingMethod.objects,
        required=True)
    shipping_charge = PriceSerializer(many=False, required=True)
    shipping_address = ShippingAddressSerializer(many=False, required=False)
    billing_address = BillingAddressSerializer(many=False, required=False)

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            return instance

        basket = attrs.get('basket')
        order_number = self.generate_order_number(basket)
        try:
            request = self.context['request']
            return self.place_order(
                order_number=order_number,
                user=request.user,
                basket=prepare_basket(basket, request),
                shipping_address=attrs.get('shipping_address'),
                shipping_method=attrs.get('shipping_method'),
                shipping_charge=attrs.get('shipping_charge'),
                billing_address=attrs.get('billing_address'),
                order_total=attrs.get('total'),
            )
        except ValueError as e:
            raise exceptions.NotAcceptable(e.message)
