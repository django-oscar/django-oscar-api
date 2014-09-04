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

    def test_admin_user(self):
        result = self.client.login(username='admin', password='admin')
        self.assertTrue(result, "Admin should be able to log in")

    def tearDown(self):
        User.objects.get(username='admin').delete()


class BasketTest(UserTest):

    def test_create_basket(self):
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
