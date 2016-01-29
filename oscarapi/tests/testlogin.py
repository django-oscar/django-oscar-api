import json
import time

from django.conf import settings
from django.contrib.sessions.models import Session
from importlib import import_module
from django.utils import timezone

from oscarapi.tests.utils import APITest
from oscarapi.utils import (
    session_id_from_parsed_session_uri,
    get_session
)

class LoginTest(APITest):

    def test_login_with_header(self):
        "Logging in with an anonymous session id header should upgrade to an authenticated session id"
        response = self.post('api-login', username='nobody', password='nobody', session_id='koe')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Session-Id', response)
        self.assertEqual(response.get('Session-Id'), 'SID:AUTH:testserver:koe', 'the session type should be upgraded to AUTH')

        # check authentication worked
        with self.settings(DEBUG=True, OSCARAPI_USER_FIELDS=('username', 'id')):
            response = self.get('api-login', session_id='koe', authenticated=True)
            parsed_response = response.data

            self.assertEqual(parsed_response['username'], 'nobody')
            self.assertEqual(parsed_response['id'], 2)

        # note that this shows that we can move a session from one user to the
        # other! This is the responsibility of the client application!
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False, DEBUG=True, OSCARAPI_USER_FIELDS=('username', 'id')):
            response = self.post('api-login', username='admin', password='admin', session_id='koe')

            self.assertEqual(response.status_code, 200)
            self.assertIn('Session-Id', response)
            self.assertEqual(response.get('Session-Id'), 'SID:AUTH:testserver:koe', 'the session type should be upgraded to AUTH')

            # check authentication worked
            response = self.get('api-login', session_id='koe', authenticated=True)
            parsed_response = response.data

            self.assertEqual(response.status_code, 200)
            self.assertEqual(parsed_response['username'], 'admin')
            self.assertEqual(parsed_response['id'], 1)

    def test_failed_login_with_header(self):
        "Failed login should not upgrade to an authenticated session"

        response = self.post('api-login', username='nobody', password='somebody', session_id='koe')

        self.assertEqual(response.status_code, 401)
        self.assertIn('Session-Id', response)
        self.assertEqual(response.get('Session-Id'), 'SID:ANON:testserver:koe', 'the session type should NOT be upgraded to AUTH')

        # check authentication didn't work
        with self.settings(DEBUG=True, OSCARAPI_USER_FIELDS=('username', 'id')):
            response = self.get('api-login')
            self.assertFalse(response.content)
            self.assertEqual(response.status_code, 204)

    def test_login_without_header(self):
        "It should be possible to login using the normal cookie session"

        response = self.post('api-login', username='nobody', password='nobody')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(self.client.session['_auth_user_id']), 2)
        self.assertNotIn('Session-Id', response)

        # check authentication worked
        with self.settings(DEBUG=True, OSCARAPI_USER_FIELDS=('username', 'id')):
            response = self.get('api-login')
            parsed_response = response.data

            self.assertEqual(parsed_response['username'], 'nobody')
            self.assertEqual(parsed_response['id'], 2)

        # using cookie sessions it is not possible to pass 1 session to another
        # user
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False, DEBUG=True, OSCARAPI_USER_FIELDS=('username', 'id')):
            response = self.post('api-login', username='admin', password='admin')

            self.assertEqual(response.status_code, 405)
            self.assertEqual(int(self.client.session['_auth_user_id']), 2)
            self.assertNotIn('Session-Id', response)

            # check we are still authenticated as nobody
            response = self.get('api-login')
            parsed_response = response.data

            self.assertEqual(parsed_response['username'], 'nobody')
            self.assertEqual(parsed_response['id'], 2)

    def test_logged_in_users_can_not_login_again_via_the_api(self):
        "It should not be possible to move a cookie session to a header session"
        self.login(username='nobody', password='nobody')
        first_key = self.client.session.session_key
        response = self.post('api-login', username='nobody', password='nobody')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.client.session.session_key, first_key, 'Since login failed, the user should have the same session')

    def test_logging_out_with_header(self):
        "After logging out, a user can not use the session id to authenticate anymore"
        with self.settings(DEBUG=True):
            engine = import_module(settings.SESSION_ENGINE)
            session = engine.SessionStore()

            self.test_login_with_header()

            parsed_session_uri = {
                'realm': 'testserver',
                'type': 'AUTH',
                'session_id': 'koe'
            }
            session_id = session_id_from_parsed_session_uri(parsed_session_uri)
            self.assertTrue(session.exists(session_id))

            response = self.delete('api-login', session_id='koe', authenticated=True)

            self.assertFalse(session.exists(session_id))
            self.assertNotIn('Session-Id', response)

            response = self.get('api-login', session_id='koe', authenticated=True)
            self.assertEqual(response.status_code, 401)

    def test_logging_out_anonymous(self):
        "After logging out, an anonymous user can not use the session id to authenticate anymore"
        with self.settings(DEBUG=True, SESSION_SAVE_EVERY_REQUEST=True):
            engine = import_module(settings.SESSION_ENGINE)
            session = engine.SessionStore()

            # get a session running
            response = self.get('api-login', session_id='koe')
            parsed_session_uri = {
                'realm': 'testserver',
                'type': 'ANON',
                'session_id': 'koe'
            }
            session_id = session_id_from_parsed_session_uri(parsed_session_uri)
            self.assertTrue(session.exists(session_id))
            self.assertEqual(response.status_code, 204)

            # delete the session
            response = self.delete('api-login', session_id='koe')

            self.assertEqual(response.status_code, 200)
            self.assertFalse(session.exists(session_id))
            self.assertNotIn('Session-Id', response)

    def test_logging_out_with_cookie(self):
        "After logging out, a user can not use the cookie to authenticate anymore"
        self.test_login_without_header()
        with self.settings(DEBUG=True):
            engine = import_module(settings.SESSION_ENGINE)
            session = engine.SessionStore()

            session_id = self.client.session.session_key
            self.assertTrue(session.exists(session_id))

            response = self.delete('api-login')
            self.assertFalse(session.exists(session_id))

            response = self.get('api-login')

            self.assertEqual(response.status_code, 204)

    def test_can_not_start_authenticated_sessions_unauthenticated(self):
        "While anonymous session will just be started when not existing yet, authenticated ones can only be created by loggin in"
        with self.settings(DEBUG=True, SESSION_SAVE_EVERY_REQUEST=True):
            response = self.get('api-login', session_id='koe', authenticated=True)
            self.assertEqual(response.status_code, 401)


class SessionTest(APITest):
    def test_get_session(self):
        """
        Even when a session has expired, get_session should return a session
        with the requested id
        """
        with self.settings(SESSION_ENGINE='django.contrib.sessions.backends.db'):
            self._run_expired_session_test_for_engine()
        with self.settings(SESSION_ENGINE='django.contrib.sessions.backends.cache'):
            self._run_expired_session_test_for_engine()
        with self.settings(SESSION_ENGINE='django.contrib.sessions.backends.file'):
            self._run_expired_session_test_for_engine()
        with self.settings(SESSION_ENGINE='django.contrib.sessions.backends.cached_db'):
            self._run_expired_session_test_for_engine()

    def _run_expired_session_test_for_engine(self):
        # establish that get_session will return the same session
        # when that session key has not yet expired.
        session = get_session('session1')
        self.assertEqual(session.session_key, 'session1')
        session['touched'] = 'writesomething'
        session.save()
        session = get_session('session1')
        self.assertEqual(session.session_key, 'session1')
        session['touched'] = 'writesomethingelse'
        session.save()
        self.assertEqual(session.session_key, 'session1')

        # when the session expires immediately, the same session should
        # still be returned.
        with self.settings(SESSION_COOKIE_AGE=-10000):
            # create a new session
            session = get_session('session2')
            self.assertEqual(session.session_key, 'session2')
            session['touched'] = 'writesomething'
            session.save()
            self.assertEqual(session.session_key, 'session2')

            # get a session with the same id, even when it has expired.
            session = get_session('session2')
            self.assertEqual(session.session_key, 'session2')
            session['touched'] = 'writesomethingelse'
            session.save()
            self.assertEqual(session.session_key, 'session2')

