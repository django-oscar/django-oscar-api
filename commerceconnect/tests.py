"""
These tests should pass nomatter in which application the commerceconnect app
is being used.
"""
import json
from oscar.core.loading import get_model
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.urlresolvers import reverse

User = get_user_model()
Basket = get_model('basket', 'Basket')


class UserTest(TestCase):
    """
    Let's do it this way instead of fixtures, because it is pretty likely
    that the User model has been changed by other people, which means the fixtures
    might not fit.
    """

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

    def test_admin_user(self):
        "Admin user can authenticate with django via the html frontend"
        result = self.client.login(username='admin', password='admin')
        self.assertTrue(result, "Admin should be able to log in")
        self.assertEqual(self.client.session['_auth_user_id'], 1)

    def test_non_admin_user(self):
        "Regular user can authenticate with django via the html frontend"
        result = self.client.login(username='nobody', password='nobody')
        self.assertTrue(result, "Nobody should be able to log in")
        self.assertEqual(self.client.session['_auth_user_id'], 2)
        
    def tearDown(self):
        User.objects.get(username='admin').delete()
        User.objects.get(username='nobody').delete()


class BasketTest(UserTest):

    def test_create_basket(self):
        self.test_admin_user()
        empty = Basket.objects.all()
        self.assertFalse(empty.exists())

        url = reverse('basket-list')
        data = {'owner': "http://localhost:8000%s" % reverse('user-detail', args=[1])}
        response = self.client.post(url, json.dumps(data), content_type='application/json', session_id="dikke lul")
        self.assertEqual(response.status_code, 201, "It should be possible for a basket to be created, for a specific user.")

        data = {}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201, "It should be possible for a basket to be created for an anonymous user.")

        self.assertEqual(Basket.objects.count(), 2, "2 baskets should after creating 2 baskets.")

    def test_retrieve_basket(self):
        pass

class LoginTest(UserTest):
    def test_login_with_header(self):
        "Logging in with an anonymous session id header should upgrade to an authenticated session id"
        url = reverse('api-login')
        data = {'username': 'nobody', 'password': 'nobody'}
        response = self.client.post(url, json.dumps(data), content_type='application/json', HTTP_SESSION_ID='SID:ANON:testserver:kak')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['_auth_user_id'], 2)
        self.assertIn('Session-Id', response)
        self.assertEqual(response.get('Session-Id'), 'SID:AUTH:testserver:kak', 'the session type should be upgraded to AUTH')

        # check authentication worked
        with self.settings(DEBUG=True, CC_USER_FIELDS=('username', 'id')):
            response = self.client.get(url, content_type='application/json', HTTP_SESSION_ID=response.get('Session-Id'))
            parsed_response = json.loads(response.content)

            self.assertEqual(parsed_response['username'], 'nobody')
            self.assertEqual(parsed_response['id'], 2)

        # note that this shows that we can move a session from one user to the
        # other! This is the responsibility of the client application!
        with self.settings(CC_BLOCK_ADMIN_API_ACCESS=False, DEBUG=True, CC_USER_FIELDS=('username', 'id')):
            data = {'username': 'admin', 'password': 'admin'}
            response = self.client.post(url, json.dumps(data), content_type='application/json', HTTP_SESSION_ID='SID:ANON:testserver:kak')

            self.assertEqual(response.status_code, 200)
            self.assertIn('Session-Id', response)
            self.assertEqual(self.client.session['_auth_user_id'], 1)
            self.assertEqual(response.get('Session-Id'), 'SID:AUTH:testserver:kak', 'the session type should be upgraded to AUTH')

            # check authentication worked
            response = self.client.get(url, content_type='application/json', HTTP_SESSION_ID=response.get('Session-Id'))
            parsed_response = json.loads(response.content)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(parsed_response['username'], 'admin')
            self.assertEqual(parsed_response['id'], 1)

    def test_failed_login_with_header(self):
        "Failed login should not upgrade to an authenticated session"
        url = reverse('api-login')
        data = {'username': 'nobody', 'password': 'somebody'}
        response = self.client.post(url, json.dumps(data), content_type='application/json', HTTP_SESSION_ID='SID:ANON:testserver:kak')

        self.assertEqual(response.status_code, 401)
        self.assertIn('Session-Id', response)
        self.assertEqual(response.get('Session-Id'), 'SID:ANON:testserver:kak', 'the session type should NOT be upgraded to AUTH')

        # check authentication didn't work
        with self.settings(DEBUG=True, CC_USER_FIELDS=('username', 'id')):
            response = self.client.get(url, content_type='application/json')
            self.assertFalse(response.content)
            self.assertEqual(response.status_code, 204)

    def test_login_without_header(self):
        "It should be possible to login using the normal cookie session"
        url = reverse('api-login')
        data = {'username': 'nobody', 'password': 'nobody'}
        response = self.client.post(url, json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['_auth_user_id'], 2)
        self.assertNotIn('Session-Id', response)

        # check authentication worked
        with self.settings(DEBUG=True, CC_USER_FIELDS=('username', 'id')):
            response = self.client.get(url, content_type='application/json')
            parsed_response = json.loads(response.content)

            self.assertEqual(parsed_response['username'], 'nobody')
            self.assertEqual(parsed_response['id'], 2)

        # using cookie sessions it is not possible to pass 1 session to another 
        # user
        with self.settings(CC_BLOCK_ADMIN_API_ACCESS=False, DEBUG=True, CC_USER_FIELDS=('username', 'id')):
            data = {'username': 'admin', 'password': 'admin'}
            response = self.client.post(url, json.dumps(data), content_type='application/json')

            self.assertEqual(response.status_code, 405)
            self.assertEqual(self.client.session['_auth_user_id'], 2)
            self.assertNotIn('Session-Id', response)

            # check we are still authenticated as nobody
            response = self.client.get(url, content_type='application/json')
            parsed_response = json.loads(response.content)

            self.assertEqual(parsed_response['username'], 'nobody')
            self.assertEqual(parsed_response['id'], 2)

    def test_logged_in_users_can_not_login_again_via_the_api(self):
        "It should not be possible to move a cookie session to a header session"
        self.test_non_admin_user()
        first_key = self.client.session.session_key
        url = reverse('api-login')
        data = {'username': 'nobody', 'password': 'nobody'}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.client.session.session_key, first_key, 'Since login failed, the user should have the same session')

    def test_logging_out(self):
        "After logging out, a user can not use the session id to authenticate anymore"
        