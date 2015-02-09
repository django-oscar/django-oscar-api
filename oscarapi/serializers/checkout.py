import warnings

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.utils.translation import gettext as _
from oscar.core import prices
from oscar.core.loading import get_class, get_model
from rest_framework import serializers, exceptions

from oscarapi.basket.operations import prepare_basket
from oscarapi.utils import (
    OscarHyperlinkedModelSerializer,
    OscarModelSerializer,
    overridable
)

OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')
ShippingAddress = get_model('order', 'ShippingAddress')
BillingAddress = get_model('order', 'BillingAddress')
Order = get_model('order', 'Order')
Basket = get_model('basket', 'Basket')
Country = get_model('address', 'Country')
Repository = get_class('shipping.repository', 'Repository')


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


class ShippingMethodSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=128)
    name = serializers.CharField(max_length=128)
    price = serializers.SerializerMethodField('calculate_price')
    
    def calculate_price(self, obj):
        price = obj.calculate(self.context.get('basket'))
        return PriceSerializer(price).data


class OrderSerializer(OscarHyperlinkedModelSerializer):
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
        fields = overridable('OSCARAPI_ORDER_FIELD', default=('number',
            'basket', 'url',
            'user', 'billing_address', 'currency', 'total_incl_tax',
            'total_excl_tax', 'shipping_incl_tax', 'shipping_excl_tax',
            'shipping_address', 'shipping_method', 'shipping_code', 'status',
            'guest_email', 'date_placed'))


class CheckoutSerializer(serializers.Serializer, OrderPlacementMixin):
    basket = serializers.HyperlinkedRelatedField(
        view_name='basket-detail', queryset=Basket.objects)
    total = PriceSerializer(many=False, required=True)
    shipping_method_code = serializers.CharField(max_length=128, required=False)
    shipping_charge = PriceSerializer(many=False, required=False)
    shipping_address = ShippingAddressSerializer(many=False, required=False)
    billing_address = BillingAddressSerializer(many=False, required=False)

    def validate(self, attrs):
        request = self.context['request']
        basket = attrs.get('basket')
        basket = prepare_basket(basket, request)
        shipping_method = self._shipping_method(
            request, basket,
            attrs.get('shipping_method_code'),
            attrs.get('shipping_address')
        )
        shipping_charge = shipping_method.calculate(basket)
        posted_shipping_charge = attrs.get('shipping_charge')

        # test submitted data.
        if posted_shipping_charge is not None and \
            not posted_shipping_charge == shipping_charge:
            message = _('Shipping price incorrect %s != %s' % (
                posted_shipping_charge, shipping_charge
            ))
            raise serializers.ValidationError(message)

        total = attrs.get('total')
        if total.excl_tax != basket.total_excl_tax:
            message = _('Total incorrect %s != %s' % (
                total.excl_tax,
                basket.total_excl_tax
            ))
            raise serializers.ValidationError(message)

        if total.tax != basket.total_tax:
            message = _('Total incorrect %s != %s' % (
                total.tax,
                basket.total_tax
            ))
            raise serializers.ValidationError(message)

        if request.user.is_anonymous() and not settings.OSCAR_ALLOW_ANON_CHECKOUT:
            message = _('Anonymous checkout forbidden')
            raise serializers.ValidationError(message)

        # update attrs with validated data.
        attrs['shipping_method'] = shipping_method
        attrs['shipping_charge'] = shipping_charge
        attrs['basket'] = basket
        return attrs

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            return instance

        try:
            basket = attrs.get('basket')
            order_number = self.generate_order_number(basket)
            request = self.context['request']

            return self.place_order(
                order_number=order_number,
                user=request.user,
                basket=basket,
                shipping_address=attrs.get('shipping_address'),
                shipping_method=attrs.get('shipping_method'),
                shipping_charge=attrs.get('shipping_charge'),
                billing_address=attrs.get('billing_address'),
                order_total=attrs.get('total'),
            )
        except ValueError as e:
            raise exceptions.NotAcceptable(e.message)

    def _shipping_method(self, request, basket,
                         shipping_method_code, shipping_address):
        repo = Repository()

        default = repo.get_default_shipping_method(
            basket=basket, 
            user=request.user,
            request=request,
            shipping_addr=shipping_address
        )

        if shipping_method_code is not None:
            methods = repo.get_shipping_methods(
                basket=basket,
                user=request.user,
                request=request,
                shipping_addr=shipping_address
            )

            find_method = (s for s in methods if s.code == shipping_method_code)
            shipping_method = next(find_method, default)
            return shipping_method

        return default

