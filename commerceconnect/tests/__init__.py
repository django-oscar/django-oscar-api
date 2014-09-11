"""
These tests should pass nomatter in which application the commerceconnect app
is being used.
"""
import json
import unittest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.importlib import import_module

from oscar.core.loading import get_model


User = get_user_model()
Basket = get_model('basket', 'Basket')


class APITest(TestCase):
    longMessage = True

    def setUp(self):
        user = User.objects.create_user(username='admin', email='admin@admin.admin', password='admin')
        user.is_staff = True
        user.is_superuser = True
        user.save()
        user = User.objects.create_user(username='nobody', email='nobody@nobody.niks', password='nobody')
        user.is_staff = False
        user.is_superuser = False
        user.save()

    def login(self, username, password):
        result =self.client.login(username=username, password=password)
        self.assertTrue(result, "%s should be able to log in" % username)
        return True

    def hlogin(self, username, password, session_id):
        response = self.post('api-login', session_id, username=username, password=password)
        self.assertEqual(response.status_code, 200, '%s should be able to login via the api' % username)
        return True

    def api_call(self, url_name, method, session_id=None, authenticated=False, **data):
        url = reverse(url_name)
        method = getattr(self.client, method.lower())
        kwargs = {
            'content_type': 'application/json',
        }
        if session_id is not None:
            auth_type = 'AUTH' if authenticated else 'ANON'
            kwargs['HTTP_SESSION_ID'] = 'SID:%s:testserver:%s' % (auth_type, session_id)

        if data:
            return method(url, json.dumps(data), **kwargs)
        else:
            return method(url, **kwargs)

    def get(self, url_name, session_id=None, authenticated=False):
        return self.api_call(url_name, 'GET', session_id=session_id, authenticated=authenticated)

    def post(self, url_name, session_id=None, authenticated=False, **data):
        return self.api_call(url_name, 'POST', session_id=session_id, authenticated=authenticated, **data)

    def put(self, url_name, session_id=None, authenticated=False, **data):
        return self.api_call(url_name, 'PUT', session_id=session_id, authenticated=authenticated, **data)

    def delete(self, url_name, session_id=None, authenticated=False):
        return self.api_call(url_name, 'DELETE', session_id=session_id, authenticated=authenticated)

    def tearDown(self):
        User.objects.get(username='admin').delete()
        User.objects.get(username='nobody').delete()


class UserTest(APITest):
    """
    Check the users are properly created bys setUp.

    Let's do it this way instead of fixtures, because it is pretty likely
    that the User model has been changed by other people, which means the fixtures
    might not fit.
    """

    def test_admin_user(self):
        "Admin user can authenticate with django via the html frontend"
        self.login('admin', 'admin')
        self.assertEqual(self.client.session['_auth_user_id'], 1)

    def test_non_admin_user(self):
        "Regular user can authenticate with django via the html frontend"
        self.login('nobody', 'nobody')
        self.assertEqual(self.client.session['_auth_user_id'], 2)

    def test_admin_header(self):
        self.hlogin('admin', 'admin', 'admin')
    
    def test_non_admin_header(self):
        self.hlogin('nobody', 'nobody', 'nobody')

class BasketTest(APITest):

    def test_basket_api_create(self):
        "The basket api create command should work with regular cookie based login"
        url = reverse('basket-list')
        empty = Basket.objects.all()
        self.assertFalse(empty.exists(), "There should be no baskets yet.")

        # anonymous        
        data = {}

        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403, "Anonymous users can not use the basket api to create baskets.")

        # authenticated
        self.login('nobody', 'nobody')
        data = {'owner': "http://testserver%s" % reverse('user-detail', args=[2])}

        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403, "Authenticated regular users can not use the basket api to create baskets.")

        # admin
        self.login('admin', 'admin')

        data = {'owner': "http://testserver%s" % reverse('user-detail', args=[1])}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201, "It should be possible for a basket to be created, for a specific user.")

        data = json.loads(response.content)
        self.assertEqual(data['owner'], "http://testserver/commerceconnect/users/1/")

        data = {}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201, "It should be possible for a basket to be created for an anonymous user.")

        self.assertEqual(Basket.objects.count(), 2, "2 baskets should after creating 2 baskets.")

    def test_basket_api_create_header(self):
        "The basket api create command should work with header based login."
        empty = Basket.open.all()
        self.assertFalse(empty.exists(), "There should be no baskets yet.")

        if self.hlogin('nobody', 'nobody', session_id='nobody'):
            response = self.post('basket-list', session_id='nobody', authenticated=True,
                owner="http://testserver%s" % reverse('user-detail', args=[2])
            )
            self.assertEqual(response.status_code, 403, "Authenticated regular users can not use the basket api to create baskets.")

        if self.hlogin('admin', 'admin', session_id='admin'):
            response = self.post('basket-list', session_id='admin', authenticated=True,
                owner="http://testserver%s" % reverse('user-detail', args=[1])
            )
            self.assertEqual(response.status_code, 201, "It should be possible for a basket to be created, for a specific user.")

            data = json.loads(response.content)
            self.assertEqual(data['owner'], "http://testserver/commerceconnect/users/1/")

        self.assertEqual(Basket.open.count(), 3, "There should be 2 baskets from loging in and 1 is created with the api.")
            
    def test_retrieve_basket(self):
        "A user can fetch their own basket with the basket API and get's the same basket every time."
        # anonymous
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['owner'], None)
        basket_id = parsed_data['id']
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)
        
        # authenticated
        self.login('nobody', 'nobody')
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['owner'], "http://testserver/commerceconnect/users/2/")
        basket_id = parsed_data['id']
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)

        # admin
        with self.settings(CC_BLOCK_ADMIN_API_ACCESS=False):
            self.login('admin', 'admin')
            response = self.get('api-basket')
            self.assertEqual(response.status_code, 200)
            parsed_data = json.loads(response.content)
            self.assertEqual(parsed_data['owner'], "http://testserver/commerceconnect/users/1/")
            basket_id = parsed_data['id']
            response = self.get('api-basket')
            self.assertEqual(response.status_code, 200)
            parsed_data = json.loads(response.content)
            self.assertEqual(parsed_data['id'], basket_id)

        self.assertEqual(Basket.open.count(), 3, "There should be 3 baskets open after 3 users accessed a basket.")

    def test_retrieve_basket_header(self):
        "Using header authentication the basket api should also work perfectly."
        # anonymous
        response = self.get('api-basket', session_id='anonymous')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['owner'], None)
        basket_id = parsed_data['id']
        response = self.get('api-basket', session_id='anonymous')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)
        
        # authenticated
        self.hlogin('nobody', 'nobody', session_id='nobody')
        response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['owner'], "http://testserver/commerceconnect/users/2/")
        basket_id = parsed_data['id']
        response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)

        # admin
        with self.settings(CC_BLOCK_ADMIN_API_ACCESS=False):
            self.hlogin('admin', 'admin', session_id='admin')
            response = self.get('api-basket', session_id='admin', authenticated=True)
            self.assertEqual(response.status_code, 200)
            parsed_data = json.loads(response.content)
            self.assertEqual(parsed_data['owner'], "http://testserver/commerceconnect/users/1/")
            basket_id = parsed_data['id']
            response = self.get('api-basket', session_id='admin', authenticated=True)
            self.assertEqual(response.status_code, 200)
            parsed_data = json.loads(response.content)
            self.assertEqual(parsed_data['id'], basket_id)

        self.assertEqual(Basket.open.count(), 3, "There should be 3 baskets open after 3 users accessed a basket.")

    def test_basket_permissions(self):
        "A regular or anonymous user should not be able to fetch someone elses basket."
        

class LoginTest(APITest):
    def test_login_with_header(self):
        "Logging in with an anonymous session id header should upgrade to an authenticated session id"
        response = self.post('api-login', username='nobody', password='nobody', session_id='koe')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['_auth_user_id'], 2)
        self.assertIn('Session-Id', response)
        self.assertEqual(response.get('Session-Id'), 'SID:AUTH:testserver:koe', 'the session type should be upgraded to AUTH')

        # check authentication worked
        with self.settings(DEBUG=True, CC_USER_FIELDS=('username', 'id')):
            response = self.get('api-login', session_id='koe', authenticated=True)
            parsed_response = json.loads(response.content)

            self.assertEqual(parsed_response['username'], 'nobody')
            self.assertEqual(parsed_response['id'], 2)

        # note that this shows that we can move a session from one user to the
        # other! This is the responsibility of the client application!
        with self.settings(CC_BLOCK_ADMIN_API_ACCESS=False, DEBUG=True, CC_USER_FIELDS=('username', 'id')):
            response = self.post('api-login', username='admin', password='admin', session_id='koe')

            self.assertEqual(response.status_code, 200)
            self.assertIn('Session-Id', response)
            self.assertEqual(self.client.session['_auth_user_id'], 1)
            self.assertEqual(response.get('Session-Id'), 'SID:AUTH:testserver:koe', 'the session type should be upgraded to AUTH')

            # check authentication worked
            response = self.get('api-login', session_id='koe', authenticated=True)
            parsed_response = json.loads(response.content)

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
        with self.settings(DEBUG=True, CC_USER_FIELDS=('username', 'id')):
            response = self.get('api-login')
            self.assertFalse(response.content)
            self.assertEqual(response.status_code, 204)

    def test_login_without_header(self):
        "It should be possible to login using the normal cookie session"

        response = self.post('api-login', username='nobody', password='nobody')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['_auth_user_id'], 2)
        self.assertNotIn('Session-Id', response)

        # check authentication worked
        with self.settings(DEBUG=True, CC_USER_FIELDS=('username', 'id')):
            response = self.get('api-login')
            parsed_response = json.loads(response.content)

            self.assertEqual(parsed_response['username'], 'nobody')
            self.assertEqual(parsed_response['id'], 2)

        # using cookie sessions it is not possible to pass 1 session to another 
        # user
        with self.settings(CC_BLOCK_ADMIN_API_ACCESS=False, DEBUG=True, CC_USER_FIELDS=('username', 'id')):
            response = self.post('api-login', username='admin', password='admin')

            self.assertEqual(response.status_code, 405)
            self.assertEqual(self.client.session['_auth_user_id'], 2)
            self.assertNotIn('Session-Id', response)

            # check we are still authenticated as nobody
            response = self.get('api-login')
            parsed_response = json.loads(response.content)

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

            session_id = self.client.session.session_key
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
            session_id = self.client.session.session_key

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
