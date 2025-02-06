from __future__ import unicode_literals
import logging

from django.views.generic import RedirectView, View
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.urls import reverse  # Updated the import path for reverse
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _  # Updated for translation

from oscar.apps.payment.exceptions import UnableToTakePayment
from oscar.core.loading import get_class, get_model

from . import facade
from .exceptions import (
    EmptyBasketException, MissingShippingAddressException,
    MissingShippingMethodException, InvalidBasket, RazorpayError
)
import razorpay

client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))

# Load views dynamically
PaymentDetailsView = get_class('checkout.views', 'PaymentDetailsView')
CheckoutSessionMixin = get_class('checkout.session', 'CheckoutSessionMixin')

ShippingAddress = get_model('order', 'ShippingAddress')
Country = get_model('address', 'Country')
Basket = get_model('basket', 'Basket')
Repository = get_class('shipping.repository', 'Repository')
Selector = get_class('partner.strategy', 'Selector')
Source = get_model('payment', 'Source')
SourceType = get_model('payment', 'SourceType')

Applicator = get_class('offer.applicator', 'Applicator')

logger = logging.getLogger('razorpay')


class PaymentView(CheckoutSessionMixin, View):
    """
    Show the razorpay payment page and record the start of a transaction.
    """

    template_name = 'rzpay/payment.html'

    def get(self, request, *args, **kwargs):
        try:
            basket = self.build_submission()['basket']
            if basket.is_empty:
                raise EmptyBasketException()
        except InvalidBasket as e:
            messages.warning(self.request, str(e))  # No need for six.text_type in Python 3
            return reverse('basket-list')
        except EmptyBasketException:
            messages.error(self.request, _("Your basket is empty"))
            return reverse('basket-list')
        except MissingShippingAddressException:
            messages.error(
                self.request, _("A shipping address must be specified"))
            return reverse('basket-list')
        except MissingShippingMethodException:
            messages.error(
                self.request, _("A shipping method must be specified"))
            return reverse('basket-list')
        else:
            # Freeze the basket so it can't be edited while the customer is
            # making the payment
            basket.freeze()

            logger.info("Starting payment for basket #%s", basket.id)
            context = self._start_razorpay_txn(basket)
            return render(request, self.template_name, context)

    def _start_razorpay_txn(self, basket, **kwargs):
        """
        Record the start of a transaction.
        """
        if basket.is_empty:
            raise EmptyBasketException()
        user = self.request.user
        amount = basket.total_incl_tax
        if self.request.user.is_authenticated:  # Updated to use property
            email = self.request.user.email
        else:
            email = self.build_submission()['order_kwargs']['guest_email']
            user = None
        txn = facade.start_razorpay_txn(basket, amount, user, email)
        from uuid import uuid4
        rz_order = client.order.create({
            "amount": int(amount * 100),
            "currency": basket.currency or getattr(settings, 'RAZORPAY_CURRENCY', 'INR'),
            "receipt": f"RCPT{uuid4().hex[:28]}",
            "notes": {
                'txn_id': txn.txnid,
            }
        })
        context = {
            "basket": basket,
            "amount": int(amount * 100),  # amount in paisa as int
            "rz_key": settings.RAZORPAY_API_KEY,
            "email": email,
            "txn_id": txn.txnid,
            "rz_order": rz_order,
            "name": getattr(settings, "RAZORPAY_VENDOR_NAME", "My Store"),
            "description": getattr(
                settings, "RAZORPAY_DESCRIPTION", "Amazing Product"
            ),
            "theme_color": getattr(
                settings, "RAZORPAY_THEME_COLOR", "#F37254"
            ),
            "logo_url": getattr(
                settings, "RAZORPAY_VENDOR_LOGO",
                "https://via.placeholder.com/150x150"
            ),
        }
        return context


class CancelResponseView(RedirectView):
    permanent = False

    def get(self, request, *args, **kwargs):
        basket = get_object_or_404(Basket, id=kwargs['basket_id'], status=Basket.FROZEN)
        basket.thaw()
        logger.info("Payment cancelled - basket #%s thawed", basket.id)
        return super().get(request, *args, **kwargs)

    def get_redirect_url(self, **kwargs):
        messages.error(self.request, _("Razorpay transaction cancelled"))
        return reverse('basket:summary')


class SuccessResponseView(PaymentDetailsView):
    preview = True

    @property
    def pre_conditions(self):
        return []

    def get(self, request, *args, **kwargs):
        """
        Fetch details about the successful transaction from Razorpay and place
        an order.
        """
        try:
            self.rz_id = request.GET['rz_id']
            self.txn_id = request.GET['txn_id']
        except KeyError:
            # Manipulation - redirect to basket page with warning message
            logger.warning("Missing GET params on success response page")
            messages.error(
                self.request,
                _("Unable to determine Razorpay transaction details"))
            return HttpResponseRedirect(reverse('basket:summary'))

        try:
            self.txn = facade.update_transaction_details(self.rz_id, self.txn_id)
        except RazorpayError:
            messages.error(
                self.request,
                _("A problem occurred communicating with Razorpay - "
                  "please try again later"))
            return HttpResponseRedirect(reverse('basket:summary'))

        # Reload frozen basket which is specified in the URL
        kwargs['basket'] = self.load_frozen_basket(kwargs['basket_id'])
        if not kwargs['basket']:
            logger.warning(
                "Unable to load frozen basket with ID %s", kwargs['basket_id']
            )
            messages.error(
                self.request,
                _("No basket was found that corresponds to your "
                  "Razorpay transaction"))
            return HttpResponseRedirect(reverse('basket:summary'))

        logger.info(
            "Basket #%s - showing preview payment id %s",
            kwargs['basket'].id, self.rz_id
        )

        basket = kwargs['basket']
        submission = self.build_submission(basket=basket)
        return self.submit(**submission)

    def load_frozen_basket(self, basket_id):
        # Lookup the frozen basket that this txn corresponds to
        try:
            basket = Basket.objects.get(id=basket_id, status=Basket.FROZEN)
        except Basket.DoesNotExist:
            return None

        # Assign strategy to basket instance
        if Selector:
            basket.strategy = Selector().strategy(self.request)

        # Re-apply any offers
        Applicator().apply(basket, self.request.user, request=self.request)

        return basket

    def build_submission(self, **kwargs):
        submission = super().build_submission(**kwargs)
        # Pass the user email so it can be stored with the order
        submission['order_kwargs']['guest_email'] = self.txn.email
        # Pass Razorpay params
        submission['payment_kwargs']['rz_id'] = self.rz_id
        submission['payment_kwargs']['txn'] = self.txn
        return submission

    def handle_payment(self, order_number, total, **kwargs):
        """
        Capture the money from the initial transaction.
        """
        try:
            confirm_txn = facade.capture_transaction(kwargs['rz_id'])
        except RazorpayError:
            raise UnableToTakePayment()
        if not confirm_txn.is_successful:
            raise UnableToTakePayment()

        # Record payment source and event
        source_type, is_created = SourceType.objects.get_or_create(name='Razorpay')
        source = Source(
            source_type=source_type,
            currency=confirm_txn.currency,
            amount_allocated=confirm_txn.amount,
            amount_debited=confirm_txn.amount
        )
        self.add_payment_source(source)
        self.add_payment_event('Settled', confirm_txn.amount, reference=confirm_txn.rz_id)