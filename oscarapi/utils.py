import operator
import hashlib
from importlib import import_module

from django.conf import settings
from django.contrib import auth
from django.core.urlresolvers import NoReverseMatch

from rest_framework import serializers, exceptions, relations
from rest_framework.reverse import reverse

from oscar.core.loading import get_class
import oscar.models.fields

Selector = get_class('partner.strategy', 'Selector')


def overridable(name, default):
    """
    Seems useless but this is for readability
    """
    return getattr(settings, name, default)


def expand_field_mapping(extra_fields):
    # This doesn't make a copy
    field_mapping = serializers.ModelSerializer.serializer_field_mapping
    field_mapping.update(extra_fields)
    return field_mapping


class OscarSerializer(object):
    field_mapping = expand_field_mapping({
        oscar.models.fields.NullCharField: serializers.CharField
    })

    def __init__(self, *args, **kwargs):
        """
        Allow the serializer to be initiated with only a subset of the
        speccified fields
        """
        fields = kwargs.pop('fields', None)
        super(OscarSerializer, self).__init__(*args, **kwargs)
        if fields:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def to_native(self, obj):
        num_fields = len(self.get_fields())
        native = super(OscarSerializer, self).to_native(obj)

        if num_fields == 1:
            _, val = next(native.iteritems())
            return val

        return native


class OscarModelSerializer(OscarSerializer, serializers.ModelSerializer):
    """
    Correctly map oscar fields to serializer fields.
    """


class OscarHyperlinkedModelSerializer(
        OscarSerializer, serializers.HyperlinkedModelSerializer):
    """
    Correctly map oscar fields to serializer fields.
    """


class DrillDownHyperlinkedIdentityField(relations.HyperlinkedIdentityField):
    def __init__(self, *args, **kwargs):
        try:
            self.extra_url_kwargs = kwargs.pop('extra_url_kwargs')
        except KeyError:
            msg = "DrillDownHyperlinkedIdentityField requires 'extra_url_args' argument"
            raise ValueError(msg)

        super(DrillDownHyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def get_extra_url_kwargs(self, obj):
        return {
            key: operator.attrgetter(path)(obj)
                for key, path in self.extra_url_kwargs.items()
        }

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        lookup_field = getattr(obj, self.lookup_field, None)
        kwargs = {self.lookup_field: lookup_field}
        kwargs.update(self.get_extra_url_kwargs(obj))
        # Handle unsaved object case
        if lookup_field is None:
            return None

        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except NoReverseMatch:
            pass

        if self.pk_url_kwarg != 'pk':
            # Only try pk lookup if it has been explicitly set.
            # Otherwise, the default `lookup_field = 'pk'` has us covered.
            kwargs = {self.pk_url_kwarg: obj.pk}
            kwargs.update(self.get_extra_url_kwargs(obj))
            try:
                return reverse(view_name, kwargs=kwargs, request=request, format=format)
            except NoReverseMatch:
                pass

        slug = getattr(obj, self.slug_field, None)
        if slug:
            # Only use slug lookup if a slug field exists on the model
            kwargs = {self.slug_url_kwarg: slug}
            kwargs.update(self.get_extra_url_kwargs(obj))
            try:
                return reverse(view_name, kwargs=kwargs, request=request, format=format)
            except NoReverseMatch:
                pass

        raise NoReverseMatch()


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
    session_id_base = u"SID:%(type)s:%(realm)s:%(session_id)s" % (
        parsed_session_uri)
    combined = session_id_base + settings.SECRET_KEY
    return hashlib.sha1(combined.encode()).hexdigest()


def get_session(session_id, raise_on_create=False):
    "get a session with the id specified."
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore(session_id)

    if not session.exists(session_id):
        if raise_on_create:
            raise exceptions.NotAuthenticated()
        else:
            session.save(must_create=True)
    else:
        # if we get an expired session from django,
        # the session key will change after calling load.
        # since the whole point of get_session is to retrieve a session
        # with axactly the key specified, we have to clear the expired
        # sessions and then get a new session.
        session.load()
        if session.session_key != session_id:
            engine.SessionStore.clear_expired()
            session = get_session(session_id, raise_on_create)

    return session
