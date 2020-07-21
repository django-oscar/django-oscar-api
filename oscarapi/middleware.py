import logging
import re

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponse
from django.utils.translation import ugettext as _

from oscar.core.loading import get_class

from rest_framework import HTTP_HEADER_ENCODING
from rest_framework import exceptions
from rest_framework import authentication

from oscarapi.basket.operations import (
    request_allows_access_to_basket,
    store_basket_in_session,
    get_basket,
)

from oscarapi.utils.loading import get_api_class
from oscarapi.utils.request import get_domain
from oscarapi.utils.session import session_id_from_parsed_session_uri, get_session
from oscarapi import models


BasketMiddleware = get_class("basket.middleware", "BasketMiddleware")
IsApiRequest = get_api_class("utils.request", "IsApiRequest")

logger = logging.getLogger(__name__)

HTTP_SESSION_ID_REGEX = re.compile(
    r"^SID:(?P<type>(?:ANON|AUTH)):(?P<realm>.*?):(?P<session_id>.+?)(?:[-:][0-9a-fA-F]+){0,2}$"
)


def parse_session_id(request):
    """Parse a session id from the request"""
    unparsed_session_id = request.META.get("HTTP_SESSION_ID", None)
    if unparsed_session_id is not None:
        parsed_session_id = HTTP_SESSION_ID_REGEX.match(unparsed_session_id)
        if parsed_session_id is not None:
            return parsed_session_id.groupdict()

    return None


def start_or_resume(session_id, session_type):
    if session_type == "ANON":
        return get_session(session_id, raise_on_create=False)

    return get_session(session_id, raise_on_create=True)


class HeaderSessionMiddleware(SessionMiddleware, IsApiRequest):
    """
    Implement session through headers:

    http://www.w3.org/TR/WD-session-id

    TODO:
    Implement gateway protection, with permission options for usage of
    header sessions. With that in place the api can be used for both trusted
    and non trusted clients, see README.rst.
    """

    def process_request(self, request):
        """
        Parse the session id from the 'Session-Id: ' header when using the api.
        """
        if self.is_api_request(request):
            try:
                parsed_session_uri = parse_session_id(request)
                if parsed_session_uri is not None:
                    domain = get_domain(request)
                    if parsed_session_uri["realm"] != domain:
                        raise exceptions.PermissionDenied(
                            _("Can not accept cookie with realm %s on realm %s")
                            % (parsed_session_uri["realm"], domain)
                        )
                    session_id = session_id_from_parsed_session_uri(parsed_session_uri)
                    request.session = start_or_resume(
                        session_id, session_type=parsed_session_uri["type"]
                    )
                    request.parsed_session_uri = parsed_session_uri

                    # since the session id is assigned by the CLIENT, there is
                    # no point in having csrf_protection. Session id's read
                    # from cookies, still need csrf!
                    request.csrf_processing_done = True
                    return None
            except exceptions.APIException as e:
                response = HttpResponse(
                    '{"reason": "%s"}' % e.detail, content_type="application/json"
                )
                response.status_code = e.status_code
                return response

        return super(HeaderSessionMiddleware, self).process_request(request)

    def process_response(self, request, response):
        """
        Add the 'Session-Id: ' header when using the api.
        """
        if (
            self.is_api_request(request)
            and getattr(request, "session", None) is not None
            and hasattr(request, "parsed_session_uri")
        ):
            session_key = request.session.session_key
            parsed_session_key = session_id_from_parsed_session_uri(
                request.parsed_session_uri
            )
            assert session_key == parsed_session_key, "%s is not equal to %s" % (
                session_key,
                parsed_session_key,
            )
            response["Session-Id"] = "SID:%(type)s:%(realm)s:%(session_id)s" % (
                request.parsed_session_uri
            )

        return super(HeaderSessionMiddleware, self).process_response(request, response)


class ApiGatewayMiddleWare(IsApiRequest):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self.is_api_request(request):
            key = authentication.get_authorization_header(request)
            key = key.decode(HTTP_HEADER_ENCODING)
            if not models.ApiKey.objects.filter(key=key).exists():
                logger.error(
                    "Invalid credentials provided for %s:%s by %s"
                    % (
                        request.method,
                        request.path,
                        request.META.get("REMOTE_ADDR", "<unknown>"),
                    )
                )
                raise PermissionDenied()

        return self.get_response(request)


class ApiBasketMiddleWare(BasketMiddleware, IsApiRequest):
    """
    Use this middleware instead of Oscar's basket middleware if you
    want to mix the api with regular oscar views.

    Oscar uses a cookie based session to store baskets for anonymous users, but
    oscarapi can not do that, because we don't want to put the burden
    of managing a cookie jar on oscarapi clients that are not websites.
    """

    def __call__(self, request):
        if self.is_api_request(request):
            request.cookies_to_delete = []
            # we should make sure that any cookie baskets are turned into
            # session baskets, since oscarapi uses only baskets from the
            # session.
            cookie_key = self.get_cookie_key(request)

            basket = self.get_cookie_basket(
                cookie_key,
                request,
                Exception("get_cookie_basket doesn't use the manager argument"),
            )

            if basket is not None:
                # when a basket exists and we are already allowed to access
                # this basket
                if request_allows_access_to_basket(request, basket):
                    pass
                else:
                    store_basket_in_session(basket, request.session)

        return super(ApiBasketMiddleWare, self).__call__(request)

    def process_response(self, request, response):
        if (
            self.is_api_request(request)
            and hasattr(request, "user")
            and request.session
        ):
            # at this point we are sure a basket can be found in the session
            # (if the session hasn't been destroyed by logging out),
            # because it is enforced in process_request.
            # We just have to make sure it is stored as a cookie, because it
            # could have been created by oscarapi.
            cookie_key = self.get_cookie_key(request)
            basket = get_basket(request)
            cookie = self.get_basket_hash(basket.id)

            # Delete any surplus cookies
            cookies_to_delete = getattr(request, "cookies_to_delete", [])
            for cookie_key in cookies_to_delete:
                response.delete_cookie(cookie_key)

            if not request.user.is_authenticated:
                response.set_cookie(
                    cookie_key,
                    cookie,
                    max_age=settings.OSCAR_BASKET_COOKIE_LIFETIME,
                    secure=settings.OSCAR_BASKET_COOKIE_SECURE,
                    httponly=True,
                )
            return response
        else:
            return super(ApiBasketMiddleWare, self).process_response(request, response)
