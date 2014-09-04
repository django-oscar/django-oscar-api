import hashlib
import re

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import reverse
from django.utils.importlib import import_module

from commerceconnect.utils import get_domain


HTTP_SESSION_ID_REGEX = re.compile(r'^SID:(?P<type>.*?):(?P<realm>.*?):(?P<session_id>.+?)(?:[-:][0-9a-fA-F]+)*$')


def parse_session_id(request):
    unparsed_session_id = request.META.get('HTTP_SESSION_ID', None)
    if unparsed_session_id is not None:
        parsed_session_id = HTTP_SESSION_ID_REGEX.match(unparsed_session_id)
        if parsed_session_id is not None:
            return parsed_session_id.groupdict()
    
    return None


def session_id_from_parsed_session_uri(parsed_session_uri):
    session_id_base = "SID:%(type)s:%(realm)s:%(session_id)s" % parsed_session_uri
    return hashlib.sha1(session_id_base + settings.SECRET_KEY).hexdigest()


def start_or_resume(session_id):
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore(session_id)

    if not session.exists(session_id):
        session.save(must_create=True)
    
    return session


class HeaderSessionMiddleware(SessionMiddleware):
    """
    Implement session through headers:

    http://www.w3.org/TR/WD-session-id
    """
    
    def process_request(self, request):
        """
        Parse the session id from the 'Session-Id: ' header when using the api.
        """
        if request.path.startswith(reverse('api-root')):
            parsed_session_uri = parse_session_id(request)
            if parsed_session_uri is not None:
                assert(parsed_session_uri['realm'] == get_domain(request))
                session_id = session_id_from_parsed_session_uri(parsed_session_uri)
                request.session = start_or_resume(session_id)
                request.parsed_session_uri = parsed_session_uri
                return None

        return super(HeaderSessionMiddleware, self).process_request(request)

    def process_response(self, request, response):
        """
        Add the 'Session-Id: ' header when using the api.
        """
        if request.path.startswith(reverse('api-root')) \
            and hasattr(request, 'session') \
            and hasattr(request, 'parsed_session_uri'):
            assert(request.session.session_key == session_id_from_parsed_session_uri(request.parsed_session_uri))
            response['Session-Id'] = 'SID:%(type)s:%(realm)s:%(session_id)s' % request.parsed_session_uri

        return super(HeaderSessionMiddleware, self).process_response(request, response)
