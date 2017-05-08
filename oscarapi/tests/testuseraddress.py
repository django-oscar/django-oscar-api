from django.core.urlresolvers import reverse

from oscarapi.tests.utils import APITest

ADDRESS = {
    "title": "Mr",
    "first_name": "Jos",
    "last_name": "Henken",
    "line1": "Roemerlaan 44",
    "line2": "",
    "line3": "",
    "line4": "Kroekingen",
    "state": "",
    "postcode": "7777KK",
    "phone_number": "+31 26 370 4887",
    "notes": "Please deliver after 5pm",
    "is_default_for_shipping": True,
    "is_default_for_billing": False,
    "country": "http://127.0.0.1:8000/api/countries/NL/",
}


class UserAddressTest(APITest):
    """
    let's check the user addresses api
    """
    fixtures = ['country']

    def test_useraddress_anonymous(self):
        url = reverse('useraddress-list')
        self.response = self.client.get(url, content_type='application/json')

        # not logged in, no glory
        self.assertEqual(self.response.status_code, 403)

    def test_useraddress_list_and_add(self):
        "Regular users can list and add own addresses"
        self.login('nobody', 'nobody')

        url = reverse('useraddress-list')
        self.response = self.client.get(url, content_type='application/json')

        # no addresses yet
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.data), 0)

        # let's create one
        self.response = self.post(url, **ADDRESS)
        self.assertEqual(self.response.status_code, 201)

        # And now there should be one
        self.response = self.client.get(url, content_type='application/json')
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.data), 1)

        # after logout we don't see anything
        self.client.logout()
        self.response = self.client.get(url, content_type='application/json')
        self.assertEqual(self.response.status_code, 403)

    def test_useraddress_update_and_delete(self):
        self.login('nobody', 'nobody')

        url = reverse('useraddress-list')
        # let's create one
        self.response = self.post(url, **ADDRESS)

        # there is one, let's go to the detail view
        self.response = self.client.get(url, content_type='application/json')
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.data), 1)

        url = self.response.data[0]['url']
        self.response = self.client.get(url, content_type='application/json')
        self.assertEqual(self.response.status_code, 200)

        # test some of the fields
        self.assertEqual(self.response.data['last_name'], "Henken")
        self.assertEqual(self.response.data['is_default_for_shipping'], True)
        self.assertEqual(
            self.response.data['notes'], "Please deliver after 5pm")

        # now update the last name
        updated_address = ADDRESS
        updated_address['last_name'] = 'Van Henken'
        self.response = self.put(url, **updated_address)
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.data['last_name'], "Van Henken")

        # refetching it should not make any difference
        self.response = self.client.get(url, content_type='application/json')
        self.assertEqual(self.response.data['last_name'], "Van Henken")

        # let's delete it
        self.response = self.client.delete(
            url, content_type='application/json')

        # it has been deleted, so a 204 should be the status code
        self.assertEqual(self.response.status_code, 204)

        # and it's gone
        url = reverse('useraddress-list')
        self.response = self.client.get(url, content_type='application/json')
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.data), 0)
