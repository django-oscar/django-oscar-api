from importlib import reload as reload_module

import json
from re import match

from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch
from django.http import SimpleCookie
from django.test import TestCase


User = get_user_model()


class APITest(TestCase):
    longMessage = True

    def setUp(self):
        user = User.objects.create_user(
            username="admin", email="admin@admin.admin", password="admin"
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()

        user = User.objects.create_user(
            username="nobody", email="nobody@nobody.niks", password="nobody"
        )
        user.is_staff = False
        user.is_superuser = False
        user.save()

        user = User.objects.create_user(
            username="somebody", email="somebody@nobody.niks", password="somebody"
        )
        user.is_staff = False
        user.is_superuser = False
        user.save()

    def login(self, username, password):
        result = self.client.login(username=username, password=password)
        self.assertTrue(result, "%s should be able to log in" % username)
        return True

    def hlogin(self, username, password, session_id):
        response = self.post(
            "api-login", session_id, username=username, password=password
        )
        self.assertEqual(
            response.status_code,
            200,
            "%s should be able to login via the api" % username,
        )
        return True

    def api_call(self, url_name, method, session_id=None, authenticated=False, **data):
        try:
            url = reverse(url_name)
        except NoReverseMatch:
            url = url_name
        method = getattr(self.client, method.lower())
        kwargs = {"content_type": "application/json"}
        if session_id is not None:
            auth_type = "AUTH" if authenticated else "ANON"
            kwargs["HTTP_SESSION_ID"] = "SID:%s:testserver:%s" % (auth_type, session_id)

        response = None
        if data:
            response = method(url, json.dumps(data), **kwargs)
        else:
            response = method(url, **kwargs)
        # throw away cookies when using session_id authentication
        if session_id is not None:
            self.client.cookies = SimpleCookie()

        return response

    def get(self, url_name, session_id=None, authenticated=False):
        return self.api_call(
            url_name, "GET", session_id=session_id, authenticated=authenticated
        )

    def post(self, url_name, session_id=None, authenticated=False, **data):
        return self.api_call(
            url_name, "POST", session_id=session_id, authenticated=authenticated, **data
        )

    def put(self, url_name, session_id=None, authenticated=False, **data):
        return self.api_call(
            url_name, "PUT", session_id=session_id, authenticated=authenticated, **data
        )

    def patch(self, url_name, session_id=None, authenticated=False, **data):
        return self.api_call(
            url_name,
            "PATCH",
            session_id=session_id,
            authenticated=authenticated,
            **data
        )

    def delete(self, url_name, session_id=None, authenticated=False):
        return self.api_call(
            url_name, "DELETE", session_id=session_id, authenticated=authenticated
        )

    def tearDown(self):
        User.objects.get(username="admin").delete()
        User.objects.get(username="nobody").delete()

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, response):
        self._response = ParsedResponse(response, self)

    @staticmethod
    def reload_modules(modules=()):
        for module in modules:
            reload_module(module)


class ParsedResponse(object):
    def __init__(self, response, unittestcase):
        self.response = response
        self.t = unittestcase

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, response):
        self._response = response
        self.status_code = response.status_code
        try:
            self.body = response.data
        except Exception:
            self.body = None

    def __getattr__(self, name):
        return getattr(self._response, name)

    def __getitem__(self, name):
        return self.body[name]

    def __len__(self):
        return len(self.body)

    def assertStatusEqual(self, code, message=None):
        self.t.assertEqual(self.status_code, code, message)

    def assertValueEqual(self, value_name, value, message=None):
        self.t.assertEqual(self[value_name], value, message)

    def assertObjectIdEqual(self, value_name, value, message=None):
        pattern = r".*?%s.*?/(?P<object_id>\d+)/?" % reverse("api-root")
        m = match(pattern, self[value_name])
        if m:
            object_id = int(m.groupdict()["object_id"])
        else:
            object_id = None
        self.t.assertEqual(object_id, value, message)

    def __str__(self):
        return str(self._response)
