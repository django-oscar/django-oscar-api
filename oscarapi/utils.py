import hashlib

from django.conf import settings
from django.contrib import auth
from django.utils.importlib import import_module
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, exceptions
from oscar.core.loading import get_class
import oscar.models.fields

Selector = get_class('partner.strategy', 'Selector')
Repository = get_class('shipping.repository', 'Repository')
NoShippingRequired = get_class('shipping.methods', 'NoShippingRequired')
CheckoutSessionData = get_class('checkout.utils', 'CheckoutSessionData')


def overridable(name, default):
    """
    Seems useless but this is for readability
    """
    return getattr(settings, name, default)


class OscarSerializer(object):
    field_mapping = dict(serializers.ModelSerializer.field_mapping, **{
        oscar.models.fields.NullCharField: serializers.CharField
    })

    def to_native(self, obj):
        num_fields = len(self.get_fields())
        native = super(OscarSerializer, self).to_native(obj)

        if num_fields == 1:
            _, val = next(native.iteritems())
            return val

        return native


class OscarStrategySerializer(serializers.Serializer):
    """Provides easy access to the price and stock information provided by
        our strategy
    """

    def __init__(self, *args, **kwargs):
        super(OscarStrategySerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        user = request.user if request is not None else None
        strategy = Selector().strategy(request=request, user=user)
        self.object.info = strategy.fetch_for_product(self.object)


class OscarModelSerializer(OscarSerializer, serializers.ModelSerializer):
    """
    Correctly map oscar fields to serializer fields.
    """


class OscarHyperlinkedModelSerializer(
        OscarSerializer, serializers.HyperlinkedModelSerializer):
    """
    Correctly map oscar fields to serializer fields.
    """


def get_domain(request):
    return request.get_host().split(':')[0]


def login_and_upgrade_session(request, user):
    "Upgrade anonymous session to authenticated session"
    parsed_session_uri = getattr(request, 'parsed_session_uri', None)

    if parsed_session_uri is not None:

        assert(parsed_session_uri['type'] == 'ANON')

        # change anonymous session to authenticated
        parsed_session_uri['type'] = "AUTH"
        session_id = session_id_from_parsed_session_uri(parsed_session_uri)

        # wipe out old anonymous session without creating a new one
        request.session.clear()
        request.session.delete()

        # start session with new session id
        request.session = get_session(session_id)

        # Mark the new session as owned by the user we are logging in.
        request.session[auth.SESSION_KEY] = user.pk
        if hasattr(user, 'get_session_auth_hash'):  # django 1.7
            request.session[auth.HASH_SESSION_KEY] = \
                user.get_session_auth_hash()

    # now login so the session can be used for authentication purposes.
    auth.login(request, user)
    request.session.save()


def session_id_from_parsed_session_uri(parsed_session_uri):
    session_id_base = "SID:%(type)s:%(realm)s:%(session_id)s" % (
        parsed_session_uri)
    return hashlib.sha1(session_id_base + settings.SECRET_KEY).hexdigest()


def get_session(session_id, raise_on_create=False):
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore(session_id)

    if not session.exists(session_id):
        if raise_on_create:
            raise exceptions.NotAuthenticated()
        else:
            session.save(must_create=True)

    return session


class GetShippingMixin(object):

    def _shipping_method(self, request, basket, shipping_method_code, shipping_address):
        repository = Repository()

        if not request.basket.is_shipping_required():
            # No shipping required - we store a special code to indicate so.
            self.checkout_session.use_shipping_method(
                NoShippingRequired().code)
            return NoShippingRequired()

        if not self.checkout_session.is_shipping_address_set():
            raise serializers.ValidationError(request, _("Please choose a shipping address"))

        methods = repository.get_shipping_methods(
                basket=basket,
                user=request.user,
                request=request,
                shipping_addr=shipping_address
            )
        if shipping_method_code is not None:

            shipping_methods = (method for method in methods if method.code == shipping_method_code)
        else:
            shipping_methods = methods
        if len(shipping_methods) > 0:
            method = shipping_methods[0]
        else:
            raise serializers.ValidationError(_('Not required shipping methods'))
        self.checkout_session.use_shipping_method(method.code)
        return method

    def _set_new_address(self, basket, address):
        self.checkout_session = CheckoutSessionData(self.request)
        address_fields = dict(
            (k, v) for (k, v) in address.__dict__.items()
            if not k.startswith('_'))
        self.checkout_session.ship_to_new_address(address_fields)