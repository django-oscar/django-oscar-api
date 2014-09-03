import re

from commerceconnect.utils import get_domain
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import reverse
from django.utils.importlib import import_module


HTTP_SESSION_ID_REGEX = re.compile(r'^SID:(?P<type>.*?):(?P<realm>.*?):(?P<session_id>.+?)(?:[-:][0-9a-fA-F]+)*$')


def parse_session_id(request):
    unparsed_session_id = request.META.get('HTTP_SESSION_ID', None)
    if unparsed_session_id is not None:
        parsed_session_id = HTTP_SESSION_ID_REGEX.match(unparsed_session_id)
        if parsed_session_id is not None:
            return parsed_session_id.groupdict()
    
    return None


def session_with_id(session_id):
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
            header_session_id = parse_session_id(request)
            if header_session_id is not None:

                request.session = session_with_id(header_session_id['session_id'])
                request.session_type = header_session_id['type']
                return None

        return super(HeaderSessionMiddleware, self).process_request(request)

    def process_response(self, request, response):
        """
        Add the 'Session-Id: ' header when using the api.
        """
        if request.path.startswith(reverse('api-root')) and hasattr(request, 'session'):
            spec = {
                'realm': get_domain(request),
                'session_id': request.session.session_key
            }
            response['Session-Id'] = 'SID::%(realm)s:%(session_id)s' % spec

        return super(HeaderSessionMiddleware, self).process_response(request, response)
