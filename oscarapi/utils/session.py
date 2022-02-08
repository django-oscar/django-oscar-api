import hashlib
from importlib import import_module

from django.conf import settings
from django.contrib import auth

from rest_framework import exceptions

from oscar.core.loading import get_class

Selector = get_class("partner.strategy", "Selector")


def login_and_upgrade_session(request, user):
    "Upgrade anonymous session to authenticated session"
    parsed_session_uri = getattr(request, "parsed_session_uri", None)

    if parsed_session_uri is not None:

        assert parsed_session_uri["type"] == "ANON"

        # change anonymous session to authenticated
        parsed_session_uri["type"] = "AUTH"
        session_id = session_id_from_parsed_session_uri(parsed_session_uri)

        # wipe out old anonymous session without creating a new one
        request.session.clear()
        request.session.delete()

        # start session with new session id
        request.session = get_session(session_id)

        # Mark the new session as owned by the user we are logging in.
        request.session[auth.SESSION_KEY] = user.pk
        if hasattr(user, "get_session_auth_hash"):  # django 1.7
            request.session[auth.HASH_SESSION_KEY] = user.get_session_auth_hash()

    # now login so the session can be used for authentication purposes.
    auth.login(request, user)
    request.session.save()


def session_id_from_parsed_session_uri(parsed_session_uri):
    session_id_base = "SID:%(type)s:%(realm)s:%(session_id)s" % (parsed_session_uri)
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
        # with exactly the key specified, we have to clear the expired
        # sessions and then get a new session.
        session.load()
        if session.session_key != session_id:
            engine.SessionStore.clear_expired()
            session = get_session(session_id, raise_on_create)

    return session
