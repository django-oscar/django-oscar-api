from django.contrib.auth import get_user_model

from oscarapi.tests.utils import APITest


User = get_user_model()


class UserTest(APITest):
    """
    Check the users are properly created bys setUp.

    Let's do it this way instead of fixtures, because it is pretty likely
    that the User model has been changed by other people, which means the
    fixtures might not fit.
    """

    def test_admin_user(self):
        "Admin user can authenticate with django via the html frontend"
        self.login('admin', 'admin')
        self.assertEqual(int(self.client.session['_auth_user_id']), 1)

    def test_non_admin_user(self):
        "Regular user can authenticate with django via the html frontend"
        self.login('nobody', 'nobody')
        self.assertEqual(int(self.client.session['_auth_user_id']), 2)

    def test_admin_header(self):
        self.hlogin('admin', 'admin', 'admin')

    def test_non_admin_header(self):
        self.hlogin('nobody', 'nobody', 'nobody')
