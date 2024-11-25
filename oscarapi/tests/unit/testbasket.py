import json
from unittest import skipIf

from unittest.mock import patch
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from oscar.core.loading import get_model

from oscarapi.basket.operations import get_basket, get_user_basket
from oscarapi.tests.utils import APITest
from oscarapi import settings


Basket = get_model("basket", "Basket")
Product = get_model("catalogue", "Product")
User = get_user_model()


class BasketTest(APITest):
    fixtures = [
        "product",
        "productcategory",
        "productattribute",
        "productclass",
        "productattributevalue",
        "category",
        "attributeoptiongroup",
        "attributeoption",
        "stockrecord",
        "partner",
        "option",
    ]

    def test_basket_api_create_not_possible(self):
        "it should not possible to create baskets with the basket-list view"
        url = reverse("basket-list")
        baskets = Basket.objects.all()

        self.assertFalse(baskets.exists(), "There should be no baskets yet.")

        # anonymous
        data = {}
        self.response = self.client.post(
            url, json.dumps(data), content_type="application/json"
        )
        self.response.assertStatusEqual(
            405, "It is not possible to use the basket-list view to create baskets."
        )

        # authenticated
        self.login("nobody", "nobody")
        data = {"owner": "http://testserver%s" % reverse("user-detail", args=[2])}

        self.response = self.client.post(
            url, json.dumps(data), content_type="application/json"
        )
        self.response.assertStatusEqual(
            405, "It is not possible to use the basket-list view to create baskets."
        )

        # admin
        self.login("admin", "admin")

        data = {"owner": "http://testserver%s" % reverse("user-detail", args=[1])}
        self.response = self.client.post(
            url, json.dumps(data), content_type="application/json"
        )
        self.response.assertStatusEqual(
            405, "It is not possible to use the basket-list view to create baskets."
        )

        self.assertEqual(Basket.objects.count(), 0)

    def test_retrieve_basket(self):
        "A user can fetch their own basket with the basket API and get's the same basket every time."
        # anonymous
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("owner", None)
        basket_id = self.response["id"]

        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)

        # authenticated
        self.login("nobody", "nobody")
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)
        self.response.assertObjectIdEqual("owner", 2)
        basket_id = self.response["id"]

        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)

        self.login("admin", "admin")
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)
        self.response.assertObjectIdEqual("owner", 1)
        basket_id = self.response["id"]

        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)

        self.assertEqual(
            Basket.objects.count(),
            3,
            "There should be 3 baskets open after 3 users accessed a basket.",
        )

    def test_retrieve_basket_header(self):
        "Using header authentication the basket api should also work perfectly."
        # anonymous
        self.response = self.get("api-basket", session_id="anonymous")
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("owner", None)
        basket_id = self.response["id"]

        self.response = self.get("api-basket", session_id="anonymous")
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)

        # authenticated
        self.hlogin("nobody", "nobody", session_id="nobody")
        self.response = self.get("api-basket", session_id="nobody", authenticated=True)
        self.response.assertStatusEqual(200)
        self.response.assertObjectIdEqual("owner", 2)
        basket_id = self.response["id"]

        self.response = self.get("api-basket", session_id="nobody", authenticated=True)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)

        # admin
        self.hlogin("admin", "admin", session_id="admin")
        self.response = self.get("api-basket", session_id="admin", authenticated=True)
        self.response.assertStatusEqual(200)
        self.response.assertObjectIdEqual("owner", 1)
        basket_id = self.response["id"]

        self.response = self.get("api-basket", session_id="admin", authenticated=True)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)

        self.assertEqual(
            Basket.objects.count(),
            3,
            "There should be 3 baskets open after 3 users accessed a basket.",
        )

    def test_basket_read_permissions(self):
        "A regular or anonymous user should not be able to fetch someone elses basket."
        # anonymous user can retrive a basket.
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response["url"]
        basket_lines = self.response["lines"]

        self.response = self.client.get(basket_url)
        self.response.assertStatusEqual(200)

        self.response = self.client.get(basket_lines)
        self.response.assertStatusEqual(200)

        # create a basket for somebody else
        b = Basket.objects.create(owner_id=2)
        self.assertEqual(str(b.owner), "nobody")
        self.assertEqual(b.pk, 2)

        # try to acces somebody else's basket (hihi).
        url = reverse("basket-detail", args=(2,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(
            403, "Script kiddies should fail to collect other users carts."
        )
        url = reverse("basket-lines-list", args=(2,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(
            403, "Script kiddies should fail to collect other users cart items."
        )

        # now try for authenticated user.
        self.login("nobody", "nobody")
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response["url"]
        basket_lines = self.response["lines"]

        self.response = self.client.get(basket_url)
        self.response.assertStatusEqual(200)

        self.response = self.client.get(basket_lines)
        self.response.assertStatusEqual(200)

        # try to acces somebody else's basket (hihi).
        url = reverse("basket-detail", args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(
            403, "Script kiddies should fail to collect other users carts."
        )

        url = reverse("basket-lines-list", args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(
            403, "Script kiddies should fail to collect other users cart items."
        )

        self.login("admin", "admin")
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response["url"]
        basket_lines = self.response["lines"]

        self.response = self.client.get(basket_url)
        self.response.assertStatusEqual(200)

        self.response = self.client.get(basket_lines)
        self.response.assertStatusEqual(200)

        # try to access somebody else's basket (hihi).
        url = reverse("basket-detail", args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(
            403, "Users cannot access other peoples baskets."
        )

        url = reverse("basket-lines-list", args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(403, "Users not access other peoples baskets.")

        self.assertEqual(
            Basket.objects.count(),
            3,
            "There should be 3 baskets open after 3 users accessed a basket.",
        )

    def test_basket_read_permissions_header(self):
        "A regular or anonymous user should not be able to fetch someone elses basket, even when authenticating with a session header."
        # anonymous user can retrieve a basket.
        self.response = self.get("api-basket", session_id="anonymous")
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response["url"]
        basket_lines = self.response["lines"]

        self.response = self.client.get(
            basket_url, HTTP_SESSION_ID="SID:ANON:testserver:anonymous"
        )
        self.response.assertStatusEqual(200)

        self.response = self.client.get(
            basket_lines, HTTP_SESSION_ID="SID:ANON:testserver:anonymous"
        )
        self.response.assertStatusEqual(200)

        # create a basket for somebody else
        b = Basket.objects.create(owner_id=2)
        self.assertEqual(str(b.owner), "nobody")
        self.assertEqual(b.pk, 2)

        # try to acces somebody else's basket (hihi).
        url = reverse("basket-detail", args=(2,))
        self.response = self.client.get(
            url, HTTP_SESSION_ID="SID:ANON:testserver:anonymous"
        )
        self.response.assertStatusEqual(
            403, "Script kiddies should fail to collect other users carts."
        )

        url = reverse("basket-lines-list", args=(2,))
        self.response = self.client.get(
            url, HTTP_SESSION_ID="SID:ANON:testserver:anonymous"
        )
        self.response.assertStatusEqual(
            403, "Script kiddies should fail to collect other users cart items."
        )

        # now try for authenticated user.
        self.hlogin("nobody", "nobody", session_id="nobody")
        self.response = self.get("api-basket", session_id="nobody", authenticated=True)
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response["url"]
        basket_lines = self.response["lines"]

        self.response = self.client.get(
            basket_url, HTTP_SESSION_ID="SID:AUTH:testserver:nobody"
        )
        self.response.assertStatusEqual(200)

        self.response = self.client.get(
            basket_lines, HTTP_SESSION_ID="SID:AUTH:testserver:nobody"
        )
        self.response.assertStatusEqual(200)

        # try to access somebody else's basket (hihi).
        url = reverse("basket-detail", args=(1,))
        self.response = self.client.get(
            url, HTTP_SESSION_ID="SID:AUTH:testserver:nobody"
        )
        self.response.assertStatusEqual(
            403, "Script kiddies should fail to collect other users carts."
        )

        url = reverse("basket-lines-list", args=(1,))
        self.response = self.client.get(
            url, HTTP_SESSION_ID="SID:AUTH:testserver:nobody"
        )
        self.response.assertStatusEqual(
            403, "Script kiddies should fail to collect other users cart items."
        )

        self.hlogin("admin", "admin", session_id="admin")
        self.response = self.get("api-basket", session_id="admin", authenticated=True)
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response["url"]
        basket_lines = self.response["lines"]

        self.response = self.client.get(
            basket_url, HTTP_SESSION_ID="SID:AUTH:testserver:admin"
        )
        self.response.assertStatusEqual(200)

        self.response = self.client.get(
            basket_lines, HTTP_SESSION_ID="SID:AUTH:testserver:admin"
        )
        self.response.assertStatusEqual(200)

        # try to access somebody else's basket (hihi).
        url = reverse("basket-detail", args=(1,))
        self.response = self.client.get(
            url, HTTP_SESSION_ID="SID:AUTH:testserver:admin"
        )
        self.response.assertStatusEqual(
            403, "Users cannot access other peoples baskets."
        )

        url = reverse("basket-lines-list", args=(1,))
        self.response = self.client.get(
            url, HTTP_SESSION_ID="SID:AUTH:testserver:admin"
        )
        self.response.assertStatusEqual(
            403, "Users cannot access other peoples baskets."
        )

        self.assertEqual(
            Basket.objects.count(),
            3,
            "There should be 3 baskets open after 3 users accessed a basket.",
        )

    def test_basket_write_permissions_anonymous(self):
        "An anonymous user should not be able to change someone elses basket."

        # anonymous user
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("status", "Open")

        # try to access the urls in the response.
        basket_id = self.response["id"]
        basket_url = self.response["url"]

        # change status to saved
        url = reverse("basket-detail", args=(basket_id,))
        self.response = self.put(url, status="Saved")
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)
        self.response.assertValueEqual("status", "Saved")

        # and back to open again
        self.response = self.put(url, status="Open")
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)
        self.response.assertValueEqual("status", "Open")

        # write a line to the basket
        line_data = {
            "basket": basket_url,
            "line_reference": "234_345",
            "product": "http://testserver/api/products/1/",
            "stockrecord": "http://testserver/api/products/1/stockrecords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0",
        }
        line_url = reverse("basket-lines-list", args=(basket_id,))
        self.response = self.post(line_url, **line_data)
        self.response.assertStatusEqual(201)

        # throw the basket away
        self.response = self.delete(url)
        self.response.assertStatusEqual(204)

        # now lets start messing around
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)
        basket_id = self.response["id"]

        # create a basket for another user.
        b = Basket.objects.create(owner_id=2)
        self.assertEqual(str(b.owner), "nobody")
        self.assertEqual(Basket.objects.count(), 2)
        nobody_basket_id = b.pk

        # try to access the urls in the response.
        basket_id = self.response["id"]
        basket_url = self.response["url"]
        url = reverse("basket-detail", args=(basket_id,))

        self.response.assertValueEqual("status", "Open")

        # try to write to someone else's basket by sending the primary key
        # along.
        self.response = self.put(url, status="Saved", id=nobody_basket_id)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual(
            "id", basket_id, "Primary key value can not be changed."
        )
        self.response.assertValueEqual("status", "Saved")

        # try to write to someone else's basket directly
        url = reverse("basket-detail", args=(nobody_basket_id,))
        self.response = self.put(url, status="Saved")
        self.response.assertStatusEqual(403)

        # try to delete someone else's basket
        self.response = self.delete(url)
        self.response.assertStatusEqual(403)

        # try adding lines to someone else's basket
        line_data = {
            "basket": "http://testserver/api/baskets/%s/" % nobody_basket_id,
            "line_reference": "234_345",
            "product": "http://testserver/api/products/1/",
            "stockrecord": "http://testserver/api/products/1/stockrecords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0",
        }
        url = reverse("basket-lines-list", args=(basket_id,))
        self.response = self.post(url, **line_data)
        self.response.assertStatusEqual(403)

    def test_basket_write_permissions_authenticated(self):
        "An authenticated user should not be able to change someone else's basket"

        # now try for authenticated user.
        self.login("nobody", "nobody")
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_id = self.response["id"]
        basket_url = self.response["url"]
        owner_url = self.response["owner"]
        self.assertIn(reverse("user-detail", args=(2,)), owner_url)
        self.response.assertValueEqual("status", "Open")

        # change status to saved
        url = reverse("basket-detail", args=(basket_id,))
        self.response = self.put(url, status="Saved")

        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)
        self.response.assertValueEqual("status", "Saved")

        # and back to open again
        self.response = self.put(url, status="Open")
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)
        self.response.assertValueEqual("status", "Open")

        # write a line to the basket
        line_data = {
            "basket": basket_url,
            "line_reference": "234_345",
            "product": "http://testserver/api/products/1/",
            "stockrecord": "http://testserver/api/products/1/stockrecords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0",
        }
        line_url = reverse("basket-lines-list", args=(basket_id,))
        self.response = self.post(line_url, **line_data)
        self.response.assertStatusEqual(201)

        # throw the basket away
        self.response = self.delete(url)
        self.response.assertStatusEqual(204)

        # now lets start messing around
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)
        basket_id = self.response["id"]

        # create a basket for another user.
        b = Basket.objects.create(owner_id=3)
        self.assertEqual(str(b.owner), "somebody")
        self.assertEqual(Basket.objects.count(), 2)
        somebody_basket_id = b.pk

        # try to access the urls in the response.
        basket_id = self.response["id"]
        basket_url = self.response["url"]
        url = reverse("basket-detail", args=(basket_id,))

        self.response.assertValueEqual("status", "Open")

        # try to write to someone else's basket by sending the primary key
        # along.
        self.response = self.put(url, status="Saved", id=somebody_basket_id)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual(
            "id", basket_id, "Primary key value can not be changed."
        )
        self.response.assertValueEqual("status", "Saved")

        # try to write to someone else's basket directly
        url = reverse("basket-detail", args=(somebody_basket_id,))
        self.response = self.put(url, status="Saved")
        self.response.assertStatusEqual(403)

        # try to delete someone else's basket
        self.response = self.delete(url)
        self.response.assertStatusEqual(403)

        # try adding lines to someone else's basket
        line_data = {
            "basket": "http://testserver/api/baskets/%s/" % somebody_basket_id,
            "line_reference": "234_345",
            "product": "http://testserver/api/products/1/",
            "stockrecord": "http://testserver/api/products/1/stockrecords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0",
        }
        url = reverse("basket-lines-list", args=(basket_id,))
        self.response = self.post(url, **line_data)
        self.response.assertStatusEqual(403)

    def test_basket_write_permissions_header_authenticated(self):
        "An authenticated user should not be able to change someone elses basket, when authenticating with session header."

        # now try for authenticated user.
        self.hlogin("nobody", "nobody", session_id="nobody")
        self.response = self.get("api-basket", session_id="nobody", authenticated=True)
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_id = self.response["id"]
        basket_url = self.response["url"]
        owner_url = self.response["owner"]
        self.assertIn(reverse("user-detail", args=(2,)), owner_url)
        self.response.assertValueEqual("status", "Open")

        # change status to saved
        url = reverse("basket-detail", args=(basket_id,))
        self.response = self.put(
            url, status="Saved", session_id="nobody", authenticated=True
        )

        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)
        self.response.assertValueEqual("status", "Saved")

        # and back to open again
        self.response = self.put(
            url, status="Open", session_id="nobody", authenticated=True
        )
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)
        self.response.assertValueEqual("status", "Open")

        # write a line to the basket
        line_data = {
            "basket": basket_url,
            "line_reference": "234_345",
            "product": "http://testserver/api/products/1/",
            "stockrecord": "http://testserver/api/products/1/stockrecords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0",
        }
        line_url = reverse("basket-lines-list", args=(basket_id,))
        self.response = self.post(
            line_url, session_id="nobody", authenticated=True, **line_data
        )
        self.response.assertStatusEqual(201)

        # throw the basket away
        self.response = self.delete(url, session_id="nobody", authenticated=True)
        self.response.assertStatusEqual(204)

        # now lets start messing around
        self.response = self.get("api-basket", session_id="nobody", authenticated=True)
        self.response.assertStatusEqual(200)
        basket_id = self.response["id"]

        # create a basket for another user.
        b = Basket.objects.create(owner_id=3)
        self.assertEqual(str(b.owner), "somebody")
        self.assertEqual(Basket.objects.count(), 2)
        somebody_basket_id = b.pk

        # try to access the urls in the response.
        basket_id = self.response["id"]
        basket_url = self.response["url"]
        url = reverse("basket-detail", args=(basket_id,))

        self.response.assertValueEqual("status", "Open")

        # try to write to someone else's basket by sending the primary key
        # along.
        self.response = self.put(
            url,
            status="Saved",
            session_id="nobody",
            authenticated=True,
            id=somebody_basket_id,
        )
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual(
            "id", basket_id, "Primary key value can not be changed."
        )
        self.response.assertValueEqual("status", "Saved")

        # try to write to someone else's basket directly
        url = reverse("basket-detail", args=(somebody_basket_id,))
        self.response = self.put(
            url, status="Saved", session_id="nobody", authenticated=True
        )
        self.response.assertStatusEqual(403)

        # try to delete someone else's basket
        self.response = self.delete(url, session_id="nobody", authenticated=True)
        self.response.assertStatusEqual(403)

        # try adding lines to someone else's basket
        line_data = {
            "basket": "http://testserver/api/baskets/%s/" % somebody_basket_id,
            "line_reference": "234_345",
            "product": "http://testserver/api/products/1/",
            "stockrecord": "http://testserver/api/products/1/stockrecords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0",
        }
        url = reverse("basket-lines-list", args=(basket_id,))
        self.response = self.post(
            url, session_id="nobody", authenticated=True, **line_data
        )
        self.response.assertStatusEqual(403)

    def test_basket_write_permissions_admin(self):
        "An admin user can not change someone else's basket."

        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            # now try for authenticated user.
            self.login("admin", "admin")
            self.response = self.get("api-basket")
            self.response.assertStatusEqual(200)

            # try to access the urls in the response.
            basket_id = self.response["id"]
            basket_url = self.response["url"]
            owner_url = self.response["owner"]
            self.assertIn(reverse("user-detail", args=(1,)), owner_url)
            self.response.assertValueEqual("status", "Open")

            # change status to saved
            url = reverse("basket-detail", args=(basket_id,))
            self.response = self.put(url, status="Saved")

            self.response.assertStatusEqual(200)
            self.response.assertValueEqual("id", basket_id)
            self.response.assertValueEqual("status", "Saved")

            # and back to open again
            self.response = self.put(url, status="Open")
            self.response.assertStatusEqual(200)
            self.response.assertValueEqual("id", basket_id)
            self.response.assertValueEqual("status", "Open")

            # write a line to the basket
            line_data = {
                "basket": basket_url,
                "line_reference": "234_345",
                "product": "http://testserver/api/products/1/",
                "stockrecord": "http://testserver/api/products/1/stockrecords/1/",
                "quantity": 3,
                "price_currency": "EUR",
                "price_excl_tax": "100.0",
                "price_incl_tax": "121.0",
            }
            line_url = reverse("basket-lines-list", args=(basket_id,))
            self.response = self.post(line_url, **line_data)
            self.response.assertStatusEqual(201)

            # throw the basket away
            self.response = self.delete(url)
            self.response.assertStatusEqual(204)

            # now lets start messing around
            self.response = self.get("api-basket")
            self.response.assertStatusEqual(200)
            basket_id = self.response["id"]

            # create a basket for another user.
            b = Basket.objects.create(owner_id=3)
            self.assertEqual(str(b.owner), "somebody")
            self.assertEqual(Basket.objects.count(), 2)
            somebody_basket_id = b.pk

            # try to access the urls in the response.
            basket_id = self.response["id"]
            basket_url = self.response["url"]
            url = reverse("basket-detail", args=(basket_id,))

            self.response.assertValueEqual("status", "Open")

            # try to write to someone else's basket by sending the primary key
            # along.
            self.response = self.put(url, status="Saved", id=somebody_basket_id)
            self.response.assertStatusEqual(200)
            self.response.assertValueEqual(
                "id", basket_id, "Primary key value can not be changed."
            )
            self.response.assertValueEqual("status", "Saved")

            # try to write to someone else's basket directly
            url = reverse("basket-detail", args=(somebody_basket_id,))
            self.response = self.put(url, status="Saved")
            self.response.assertStatusEqual(403)

            # try adding lines to someone else's basket
            line_data = {
                "basket": "http://testserver/api/baskets/%s/" % somebody_basket_id,
                "line_reference": "234_345",
                "product": "http://testserver/api/products/1/",
                "stockrecord": "http://testserver/api/products/1/stockrecords/1/",
                "quantity": 3,
                "price_currency": "EUR",
                "price_excl_tax": "100.0",
                "price_incl_tax": "121.0",
            }
            zurl = reverse("basket-lines-list", args=(basket_id,))
            self.response = self.post(zurl, **line_data)
            self.response.assertStatusEqual(403)

            # try to delete someone else's basket
            self.response = self.delete(url)
            self.response.assertStatusEqual(403)

    def test_basket_write_permissions_header_admin(self):
        "An admin user can not change someone else's basket, even when authenticating with session header."

        # now try for authenticated user.
        self.hlogin("admin", "admin", session_id="admin")
        self.response = self.get("api-basket", session_id="admin", authenticated=True)
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_id = self.response["id"]
        basket_url = self.response["url"]
        owner_url = self.response["owner"]
        self.assertIn(reverse("user-detail", args=(1,)), owner_url)
        self.response.assertValueEqual("status", "Open")

        # change status to saved
        url = reverse("basket-detail", args=(basket_id,))
        self.response = self.put(
            url, status="Saved", session_id="admin", authenticated=True
        )

        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)
        self.response.assertValueEqual("status", "Saved")

        # and back to open again
        self.response = self.put(
            url, status="Open", session_id="admin", authenticated=True
        )
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("id", basket_id)
        self.response.assertValueEqual("status", "Open")

        # write a line to the basket
        line_data = {
            "basket": basket_url,
            "line_reference": "234_345",
            "product": "http://testserver/api/products/1/",
            "stockrecord": "http://testserver/api/products/1/stockrecords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0",
        }
        line_url = reverse("basket-lines-list", args=(basket_id,))
        self.response = self.post(
            line_url, session_id="admin", authenticated=True, **line_data
        )
        self.response.assertStatusEqual(201)

        # throw the basket away
        self.response = self.delete(url, session_id="admin", authenticated=True)
        self.response.assertStatusEqual(204)

        # now lets start messing around
        self.response = self.get("api-basket", session_id="admin", authenticated=True)
        self.response.assertStatusEqual(200)
        basket_id = self.response["id"]

        # create a basket for another user.
        b = Basket.objects.create(owner_id=3)
        self.assertEqual(str(b.owner), "somebody")
        self.assertEqual(Basket.objects.count(), 2)
        somebody_basket_id = b.pk

        # try to access the urls in the response.
        basket_id = self.response["id"]
        basket_url = self.response["url"]
        url = reverse("basket-detail", args=(basket_id,))

        self.response.assertValueEqual("status", "Open")

        # try to write to someone else's basket by sending the primary key
        # along.
        self.response = self.put(
            url,
            status="Saved",
            session_id="admin",
            authenticated=True,
            id=somebody_basket_id,
        )
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual(
            "id", basket_id, "Primary key value can not be changed."
        )
        self.response.assertValueEqual("status", "Saved")

        # try to write to someone else's basket directly
        url = reverse("basket-detail", args=(somebody_basket_id,))
        self.response = self.put(
            url, status="Saved", session_id="admin", authenticated=True
        )
        self.response.assertStatusEqual(403)

        # try adding lines to someone else's basket
        line_data = {
            "basket": "http://testserver/api/baskets/%s/" % somebody_basket_id,
            "line_reference": "234_345",
            "product": "http://testserver/api/products/1/",
            "stockrecord": "http://testserver/api/products/1/stockrecords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0",
        }
        zurl = reverse("basket-lines-list", args=(basket_id,))
        self.response = self.post(
            zurl, session_id="admin", authenticated=True, **line_data
        )
        self.response.assertStatusEqual(403)

        # try to delete someone else's basket
        self.response = self.delete(url, session_id="admin", authenticated=True)
        self.response.assertStatusEqual(403)

    def test_add_product_anonymous(self):
        "Test if an anonymous user can add a product to his basket"
        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.response.assertStatusEqual(200)

        self.response = self.get(self.response["lines"])
        self.assertEqual(len(self.response.body), 1)
        line0 = self.response.body[0]
        self.assertEqual(line0["product"], "http://testserver/api/products/1/")
        self.assertEqual(line0["quantity"], 5)

    def test_add_product_authenticated(self):
        "Test if an authenticated user can add a product to his basket"
        self.login("nobody", "nobody")
        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.response.assertStatusEqual(200)

        self.response = self.get(self.response["lines"])
        self.assertEqual(len(self.response.body), 1)
        line0 = self.response.body[0]
        self.assertEqual(line0["product"], "http://testserver/api/products/1/")
        self.assertEqual(line0["quantity"], 5)

    @patch("oscarapi.views.basket.signals.basket_addition.send")
    def test_add_product_basket_addition_signal_send(self, mock):
        """The oscar `basket_addition` signal should be send when adding a product"""
        self.login("nobody", "nobody")
        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )

        self.assertTrue(mock.called)

        signal_arguments = mock.call_args[1]
        self.assertEqual(signal_arguments["product"], Product.objects.get(pk=1))
        self.assertEqual(signal_arguments["user"].username, "nobody")

        # see if we can get the basket from the request
        basket = get_basket(signal_arguments["request"])
        self.assertTrue(isinstance(basket, Basket))

    def test_basket_line_permissions(self):
        "A user's Basket lines can not be viewed by another user in any way."
        self.login("nobody", "nobody")
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)

        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.response = self.get(self.response["lines"])
        line0 = self.response.body[0]
        line0url = line0["url"]

        self.response = self.get(line0url)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("product", "http://testserver/api/products/1/")
        self.response.assertValueEqual("quantity", 5)

        # now let's try to cheat
        self.login("somebody", "somebody")
        self.response = self.get(line0url)
        self.response.assertStatusEqual(404)

    def test_basket_line_permissions_header(self):
        "A user's Basket lines can not be viewed by another user in any way, even with header authentication"
        self.hlogin("nobody", "nobody", session_id="nobody")
        self.response = self.get("api-basket", session_id="nobody", authenticated=True)
        self.response.assertStatusEqual(200)

        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
            session_id="nobody",
            authenticated=True,
        )
        self.response = self.get(
            self.response["lines"], session_id="nobody", authenticated=True
        )

        line0 = self.response.body[0]
        line0url = line0["url"]

        self.response = self.get(line0url, session_id="nobody", authenticated=True)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("product", "http://testserver/api/products/1/")
        self.response.assertValueEqual("quantity", 5)

        # now let's try to cheat
        self.hlogin("somebody", "somebody", session_id="somebody")
        self.response = self.get(line0url, session_id="somebody", authenticated=True)
        self.response.assertStatusEqual(404)

    def test_frozen_basket_can_not_be_accessed(self):
        "Prove that frozen baskets can no longer be accessed by the user."
        self.login("nobody", "nobody")
        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("status", "Open")

        # change status to saved
        url = reverse("basket-detail", args=(self.response["id"],))
        self.response = self.put(url, status="Frozen")
        self.response.assertValueEqual("status", "Frozen")

        self.response = self.get(url)
        self.response.assertStatusEqual(404)

    def test_frozen_basket_can_not_be_accessed_header(self):
        "Prove that frozen baskets can no longer be accessed by the user, even with header authentication"
        self.hlogin("nobody", "nobody", session_id="nobody")
        self.response = self.get("api-basket", session_id="nobody", authenticated=True)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("status", "Open")

        # change status to saved
        url = reverse("basket-detail", args=(self.response["id"],))
        self.response = self.put(
            url, status="Frozen", session_id="nobody", authenticated=True
        )
        self.response.assertValueEqual("status", "Frozen")

        self.response = self.get(url, session_id="nobody", authenticated=True)
        self.response.assertStatusEqual(404)

    def test_add_product_limit_basket(self):
        """Test if an anonymous user cannot add more than two products to his
        basket when amount of baskets is limited
        """
        with self.settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=2):
            self.response = self.post(
                "api-basket-add-product",
                url="http://testserver/api/products/1/",
                quantity=3,
            )
            self.response.assertStatusEqual(406)

    def test_total_prices_anonymous(self):
        "Test if the prices calculated by the basket are ok"
        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("total_incl_tax", "50.00")

    def test_add_product_above_stock(self):
        """Test if an anonymous user cannot add more products to his
        basket when stock is not sufficient
        """
        with self.subTest("Single request"):
            self.response = self.post(
                "api-basket-add-product",
                url="http://testserver/api/products/1/",
                quantity=25,
            )
            self.response.assertStatusEqual(406)

        with self.subTest("Sequential requests"):
            self.response = self.post(
                "api-basket-add-product",
                url="http://testserver/api/products/1/",
                quantity=20,
            )
            self.response.assertStatusEqual(200)

            self.response = self.post(
                "api-basket-add-product",
                url="http://testserver/api/products/1/",
                quantity=20,
            )
            self.response.assertStatusEqual(406)

    def test_adjust_basket_line_quantity(self):
        """Test if we can update the quantity of a line"""
        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.response.assertStatusEqual(200)

        self.response = self.get("api-basket")
        self.response.assertStatusEqual(200)

        # Get the basket lines, and update the quantity to 4
        self.response = self.get(self.response["lines"])
        basket_line_url = self.response.data[0]["url"]
        self.response = self.patch(basket_line_url, quantity=4)
        self.response.assertStatusEqual(200)

        # see if it's updated
        self.response = self.get(basket_line_url)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("quantity", 4)

    def test_add_put_product_option(self):
        """Test if we can add and update the options of a line"""

        # first select the first option available (which is color)
        self.response = self.get("http://localhost:8000/api/options/")
        option_url = self.response.json()[0]["url"]

        # add the option to the basket line
        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=1,
            options=[{"option": option_url, "value": "red"}],
        )
        self.response.assertStatusEqual(200)

        # Get the basket line, and see our option is there
        self.response = self.get("api-basket")
        basket_line_url = self.get(self.response["lines"]).data[0]["url"]
        self.response = self.get(basket_line_url)
        attribute = self.response.json()["attributes"][0]
        self.assertEqual(attribute["value"], "red")

        # now update it to blue
        self.response = self.patch(attribute["url"], value="blue")
        self.response.assertStatusEqual(200)

        # check that it's updated
        self.response = self.get(basket_line_url)
        attribute = self.response.json()["attributes"][0]
        self.assertEqual(attribute["value"], "blue")
        return attribute

    def test_product_option_write_permissions_authenticated(self):
        """Another user wants to update my color, but we don't allow that"""
        attribute = self.test_add_put_product_option()
        self.hlogin("somebody", "somebody", session_id="somebody")
        self.response = self.put(attribute["url"], value="Hack HAHAHAHA")
        self.response.assertStatusEqual(
            403, "Other users cannot update my line attributes"
        )

    def test_get_user_basket_with_multiple_baskets(self):
        user = User.objects.get(username="nobody")
        Basket.open.create(owner=user)
        Basket.open.create(owner=user)
        self.assertEqual(Basket.open.count(), 2)

        # get_user_basket will fix this automatically for us
        user_basket = get_user_basket(user)
        self.assertEqual(Basket.open.count(), 1)
        self.assertEqual(user_basket, Basket.open.first())


@skipIf(settings.BLOCK_ADMIN_API_ACCESS, "Admin API is enabled")
class BasketAdminTest(APITest):
    """
    Test suite for admin basket list operations.
    Covers access permissions, pagination, and ordering.
    """

    fixtures = [
        "product",
        "productcategory",
        "productattribute",
        "productclass",
        "productattributevalue",
        "category",
        "attributeoptiongroup",
        "attributeoption",
        "stockrecord",
        "partner",
        "option",
    ]

    def test_basket_admin_list_access(self):
        """
        Test access permissions for basket list view.

        Verifies that:
        - Unauthenticated users are forbidden
        - Standard users are forbidden
        - Admin users can access the list
        """
        url = reverse("admin-basket-list")

        # Test unauthenticated access
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # Test standard user access
        self.login("nobody", "nobody")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # Test admin access
        self.login("admin", "admin")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_basket_admin_list_pagination(self):
        """
        Test pagination functionality for basket list view.

        Checks:
        - Default page size is 100
        - Custom page size works correctly
        - Next page link is present
        """

        # Create baskets for testing
        admin_user = User.objects.get(username="admin")
        for _ in range(300):
            Basket.objects.create(owner=admin_user)

        self.login("admin", "admin")
        url = reverse("admin-basket-list")

        # Test first page pagination
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 100)

        # Check next link exists on first page
        self.assertIsNotNone(
            response.data["next"], "Next page link should be present on first page"
        )

        # Verify no previous link on first page
        self.assertIsNone(
            response.data["previous"], "First page should not have a previous link"
        )

        # Get the next page
        next_page_url = response.data["next"]
        next_page_response = self.client.get(next_page_url)

        self.assertEqual(next_page_response.status_code, 200)
        self.assertEqual(len(next_page_response.data["results"]), 100)

        # Check links on second page
        self.assertIsNotNone(
            next_page_response.data["next"],
            "Next page link should be present on second page",
        )
        self.assertIsNotNone(
            next_page_response.data["previous"],
            "Second page should have a previous link",
        )

        # Test custom page size
        response = self.client.get(f"{url}?page_size=5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 5)

    def test_basket_admin_list_ordering(self):
        """
        Test ordering of basket list view.

        Verifies that baskets are ordered by ID in descending order.
        """
        # Create baskets for testing
        admin_user = User.objects.get(username="admin")
        for _ in range(200):
            Basket.objects.create(owner=admin_user)

        self.login("admin", "admin")
        url = reverse("admin-basket-list")

        # Fetch and verify ordering
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        basket_ids = [basket["id"] for basket in response.data["results"]]
        self.assertEqual(basket_ids, sorted(basket_ids, reverse=True))

    def test_assign_basket_strategy_call_frequency(self):
        admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"is_staff": True, "password": "admin"}
        )
        total_baskets = 350

        # Populate baskets for the test
        Basket.objects.bulk_create(
            [Basket(owner=admin_user) for _ in range(total_baskets)]
        )

        # Log in as admin
        self.client.login(username="admin", password="admin")

        url = reverse("admin-basket-list")

        # Mock assign_basket_strategy and bypass serialization
        with patch("oscarapi.views.admin.basket.assign_basket_strategy") as mock_assign:
            with patch(
                "oscarapi.serializers.basket.BasketSerializer.to_representation",
                return_value={},
            ):
                self.client.get(url)

        # Assert that the mock was called exactly 100 times instead of 350
        self.assertEqual(
            mock_assign.call_count,
            100,
            f"First page should have 100 assign_basket_strategy calls, got {mock_assign.call_count}",
        )


@override_settings(
    MIDDLEWARE=(
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "oscarapi.middleware.ApiBasketMiddleWare",
        "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    )
)
class ApiBasketMiddleWareTest(APITest):
    fixtures = [
        "product",
        "productcategory",
        "productattribute",
        "productclass",
        "productattributevalue",
        "category",
        "attributeoptiongroup",
        "attributeoption",
        "stockrecord",
        "partner",
        "option",
    ]

    def test_basket_login_logout(self):
        self.assertEqual(
            Basket.objects.count(), 0, "Initially there should be no baskets"
        )

        # add something to the anonymous basket, so we get a cookie basket
        url = reverse("basket:add", kwargs={"pk": 1})
        post_params = {"child_id": 2, "action": "add", "quantity": 5}
        response = self.client.post(url, post_params, follow=True)

        self.assertEqual(
            Basket.objects.count(),
            1,
            "After posting to the basket, 1 basket should be created.",
        )
        self.assertIn(
            "oscar_open_basket",
            self.client.cookies,
            "An basket cookie should have been created",
        )
        self.assertStartsWith(self.client.cookies["oscar_open_basket"].value, "1")

        # retrieve the basket with oscarapi.
        self.response = self.get("api-basket")
        self.response.assertValueEqual(
            "owner", None, "The basket should not have an owner"
        )
        self.response.assertValueEqual("id", 1)
        self.assertStartsWith(self.client.cookies["oscar_open_basket"].value, "1")

        # now lets log in with oscarapi
        response = self.post("api-login", username="nobody", password="nobody")
        # and lets retrieve the basket
        self.response = self.get("api-basket")
        self.response.assertValueEqual(
            "owner",
            "http://testserver/api/users/2/",
            "the basket after login should have an owner",
        )
        self.assertEqual(
            self.client.cookies["oscar_open_basket"].value,
            "1:Rdm76bzEHM-N1G6WSTj0Zu9ByZ80a8ggxSkqqvGbC6s",
            "After logging out the cookie unfortunately does not go away",
        )

        response = self.client.post(url, post_params, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Basket.objects.count(), 2)
        self.assertEqual(
            self.client.cookies["oscar_open_basket"].value,
            "",
            "The basket cookie should be removed",
        )

        self.response = self.delete("api-login")
        self.assertStartsWith(
            self.client.cookies["oscar_open_basket"].value,
            "",
            "After loging out, nothing happened to the basket cookie",
        )

        self.response = self.get("api-basket")
        self.response.assertValueEqual(
            "owner", None, "The logged out user's basket should not have an owner"
        )
        self.assertEqual(
            Basket.objects.count(),
            3,
            "A new basket should be created for the anonymous (logged out) user",
        )
        self.assertStartsWith(
            self.client.cookies["oscar_open_basket"].value,
            "3",
            "The basket cookie is re-established after accessing the basket when logged out",
        )
