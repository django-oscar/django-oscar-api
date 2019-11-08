from copy import deepcopy

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.transaction import atomic

from oscarapi.tests.utils import APITest

User = get_user_model()

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

    fixtures = ["country"]

    def test_useraddress_anonymous(self):
        url = reverse("useraddress-list")
        self.response = self.client.get(url, content_type="application/json")

        # not logged in, no glory
        self.assertEqual(self.response.status_code, 403)

    def test_useraddress_list_and_add(self):
        "Regular users can list and add own addresses"
        self.login("nobody", "nobody")

        url = reverse("useraddress-list")
        self.response = self.client.get(url, content_type="application/json")

        # no addresses yet
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.data), 0)

        # let's create one
        self.response = self.post(url, **ADDRESS)
        self.assertEqual(self.response.status_code, 201)

        # And now there should be one
        self.response = self.client.get(url, content_type="application/json")
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.data), 1)

        # after logout we don't see anything
        self.client.logout()
        self.response = self.client.get(url, content_type="application/json")
        self.assertEqual(self.response.status_code, 403)

    # atomic is needed because of the teardown of this testcase
    @atomic
    def test_useraddress_duplicate(self):
        "Duplicate addresses raise an integrityerror, let's catch this"
        self.login("nobody", "nobody")

        url = reverse("useraddress-list")
        self.response = self.client.get(url, content_type="application/json")

        # let's create one
        self.response = self.post(url, **ADDRESS)
        self.assertEqual(self.response.status_code, 201)

        # And now there should be one
        self.response = self.client.get(url, content_type="application/json")
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.data), 1)

        # now we create the same address and this is not possible
        self.response = self.post(url, **ADDRESS)
        self.assertEqual(self.response.status_code, 406)

    def test_useraddress_update_and_delete(self):
        "Regular users can update and delete their own addresses"
        self.login("nobody", "nobody")

        url = reverse("useraddress-list")
        # let's create one
        self.response = self.post(url, **ADDRESS)

        # there is one, let's go to the detail view
        self.response = self.client.get(url, content_type="application/json")
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.data), 1)

        url = self.response.data[0]["url"]
        self.response = self.client.get(url, content_type="application/json")
        self.assertEqual(self.response.status_code, 200)

        # test some of the fields
        self.assertEqual(self.response.data["last_name"], "Henken")
        self.assertEqual(self.response.data["is_default_for_shipping"], True)
        self.assertEqual(self.response.data["notes"], "Please deliver after 5pm")

        # now update the last name
        updated_address = deepcopy(ADDRESS)
        updated_address["last_name"] = "Van Henken"
        self.response = self.put(url, **updated_address)
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.data["last_name"], "Van Henken")

        # refetching it should not make any difference
        self.response = self.client.get(url, content_type="application/json")
        self.assertEqual(self.response.data["last_name"], "Van Henken")

        # let's delete it
        self.response = self.client.delete(url, content_type="application/json")

        # it has been deleted, so a 204 should be the status code
        self.assertEqual(self.response.status_code, 204)

        # and it's gone
        url = reverse("useraddress-list")
        self.response = self.client.get(url, content_type="application/json")
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.data), 0)

    def test_address_security(self):
        "Make sure we can't access addresses of other users"
        # first login as the first user
        self.login("nobody", "nobody")

        nobodys_address = deepcopy(ADDRESS)
        nobodys_address["last_name"] = "Nobody"
        url = reverse("useraddress-list")
        self.response = self.post(url, **nobodys_address)

        # save the address url
        nobodys_address_url = self.response.data["url"]

        # and logout
        self.client.logout()

        # and now as the other one
        self.login("somebody", "somebody")
        url = reverse("useraddress-list")
        somebodys_address = deepcopy(ADDRESS)
        somebodys_address["last_name"] = "Somebody"
        self.response = self.post(url, **somebodys_address)

        # save the address url
        somebodys_address_url = self.response.data["url"]

        # 'somebody' should not be able to access the address
        # created by 'nobody'
        self.response = self.client.get(
            nobodys_address_url, content_type="application/json"
        )
        self.assertEqual(self.response.status_code, 404)

        # and we can't delete it either
        self.response = self.client.delete(url, content_type="application/json")
        self.assertEqual(self.response.status_code, 405)

        # logout and login again with nobody
        self.client.logout()
        self.login("nobody", "nobody")

        # 'nobody' should not be able to access the address
        # created by 'somebody'
        self.response = self.client.get(
            somebodys_address_url, content_type="application/json"
        )
        self.assertEqual(self.response.status_code, 404)

        # and we can't update it either
        somebodys_address["last_name"] = "Hacked by nobody"
        self.response = self.put(somebodys_address_url, **somebodys_address)
        self.assertEqual(self.response.status_code, 404)

        # now try to change the owner of my own address to 'somebody'
        self.response = self.client.get(nobodys_address_url)
        nobody_address = self.response.data
        nobody_address["last_name"] = "Hacked by somebody"
        nobody_address["user"] = User.objects.get(username="somebody").id
        self.response = self.put(nobodys_address_url, **nobody_address)

        # oscarapi won't choke because it will just ignore the user param
        self.assertEqual(self.response.status_code, 200)
        self.response = self.client.get(nobodys_address_url)

        # so in the end we only updated our own address
        self.assertEqual(self.response.data["last_name"], "Hacked by somebody")

        # to be sure: somebody has only one address
        self.client.logout()
        self.login("somebody", "somebody")

        url = reverse("useraddress-list")
        self.response = self.client.get(url, content_type="application/json")
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.data), 1)
