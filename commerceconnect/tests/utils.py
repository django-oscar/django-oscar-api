import json

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, NoReverseMatch
from django.test import TestCase


User = get_user_model()


class APITest(TestCase):
    longMessage = True

    def setUp(self):
        user = User.objects.create_user(
            username='admin',
            email='admin@admin.admin',
            password='admin'
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()

        user = User.objects.create_user(
            username='nobody',
            email='nobody@nobody.niks',
            password='nobody'
        )
        user.is_staff = False
        user.is_superuser = False
        user.save()

        user = User.objects.create_user(
            username='somebody',
            email='somebody@nobody.niks',
            password='somebody'
        )
        user.is_staff = False
        user.is_superuser = False
        user.save()

    def login(self, username, password):
        result = self.client.login(username=username, password=password)
        self.assertTrue(result, "%s should be able to log in" % username)
        return True

    def hlogin(self, username, password, session_id):
        response = self.post('api-login', session_id,
                             username=username, password=password)
        self.assertEqual(response.status_code, 200,
                         '%s should be able to login via the api' % username)
        return True

    def api_call(self, url_name, method, session_id=None,
                 authenticated=False, **data):
        try:
            url = reverse(url_name)
        except NoReverseMatch:
            url = url_name

        method = getattr(self.client, method.lower())
        kwargs = {
            'content_type': 'application/json',
        }
        if session_id is not None:
            auth_type = 'AUTH' if authenticated else 'ANON'
            kwargs['HTTP_SESSION_ID'] = 'SID:%s:testserver:%s' % (
                auth_type, session_id)

        if data:
            return method(url, json.dumps(data), **kwargs)
        else:
            return method(url, **kwargs)

    def get(self, url_name, session_id=None, authenticated=False):
        return self.api_call(
            url_name, 'GET',
            session_id=session_id,
            authenticated=authenticated
        )

    def post(self, url_name, session_id=None, authenticated=False, **data):
        return self.api_call(
            url_name, 'POST',
            session_id=session_id,
            authenticated=authenticated,
            **data
        )

    def put(self, url_name, session_id=None, authenticated=False, **data):
        return self.api_call(
            url_name, 'PUT',
            session_id=session_id,
            authenticated=authenticated,
            **data
        )

    def delete(self, url_name, session_id=None, authenticated=False):
        return self.api_call(
            url_name, 'DELETE',
            session_id=session_id,
            authenticated=authenticated
        )

    def tearDown(self):
        User.objects.get(username='admin').delete()
        User.objects.get(username='nobody').delete()

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, response):
        self._response = ParsedReponse(response, self)
    
class ParsedReponse(object):
    def __init__(self, response, unittestcase):
        self.response = response
        self.t = unittestcase

    @property
    def response(self):
        return self._response
    
    @response.setter
    def response(self, response):
        self._response = response
        self.body = json.loads(response.content)
        self.status_code = response.status_code

    def __getattr__(self, name):
        return self._response.__getattr__(name)
    
    def __getitem__(self, name):
        return self.body[name]
    
    def assertStatusEqual(self, code, message=None):
        self.t.assertEqual(self.status_code, code, message)
    
    def assertValueEqual(self, value_name, value, message=None):
        self.t.assertEqual(self[value_name], value, message)
