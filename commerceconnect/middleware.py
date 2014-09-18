import re

from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse
from django.utils.translation import ugettext as _
from rest_framework import exceptions

from commerceconnect.utils import (
    get_domain,
    session_id_from_parsed_session_uri,
    get_session
)

HTTP_SESSION_ID_REGEX = re.compile(
    r'^SID:(?P<type>(?:ANON|AUTH)):(?P<realm>.*?):(?P<session_id>.+?)(?:[-:][0-9a-fA-F]+)*$')


def parse_session_id(request):
    unparsed_session_id = request.META.get('HTTP_SESSION_ID', None)
    if unparsed_session_id is not None:
        parsed_session_id = HTTP_SESSION_ID_REGEX.match(unparsed_session_id)
        if parsed_session_id is not None:
            return parsed_session_id.groupdict()

    return None


def start_or_resume(session_id, session_type):
    if session_type == 'ANON':
        return get_session(session_id, raise_on_create=False)

    return get_session(session_id, raise_on_create=True)


class HeaderSessionMiddleware(SessionMiddleware):
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
        if request.path.startswith(reverse('api-root')):
            try:
                parsed_session_uri = parse_session_id(request)
                if parsed_session_uri is not None:
                    domain = get_domain(request)
                    if parsed_session_uri['realm'] != domain:
                        raise exceptions.NotAcceptable(
                            _('Can not accept cookie with realm %s on realm %s') % (
                                parsed_session_uri['realm'],
                                domain
                            )
                        )
                    session_id = session_id_from_parsed_session_uri(
                        parsed_session_uri)
                    request.session = start_or_resume(
                        session_id, session_type=parsed_session_uri['type'])
                    request.parsed_session_uri = parsed_session_uri

                    # since the session id is assigned by the CLIENT, there is
                    # no point in having csrf_protection. Session id's read
                    # from cookies, still need csrf!
                    request.csrf_processing_done = True
                    return None
            except exceptions.APIException as e:
                response = HttpResponse('{"reason": "%s"}' % e.detail)
                response.status_code = e.status_code
                return response

        return super(HeaderSessionMiddleware, self).process_request(request)

    def process_response(self, request, response):
        """
        Add the 'Session-Id: ' header when using the api.
        """
        if request.path.startswith(reverse('api-root')) \
                and getattr(request, 'session', None) is not None \
                and hasattr(request, 'parsed_session_uri'):
            assert(request.session.session_key ==
                   session_id_from_parsed_session_uri(
                       request.parsed_session_uri))
            response['Session-Id'] = \
                'SID:%(type)s:%(realm)s:%(session_id)s' % (
                    request.parsed_session_uri)

        return super(HeaderSessionMiddleware, self).process_response(
            request, response)
