from decimal import Decimal
from mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test.client import RequestFactory

from oscar.core.loading import get_model

from rest_framework.response import Response
from oscarapi.tests.utils import APITest

from oscarapi.serializers.checkout import CheckoutSerializer

Basket = get_model("basket", "Basket")
User = get_user_model()
Order = get_model("order", "Order")


class CheckoutTest(APITest):
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
        "orderanditemcharges",
        "country",
    ]

    def _get_common_payload(self, basket_url):
        return {
            "basket": basket_url,
            "guest_email": "henk@example.com",
            "total": "50.00",
            "shipping_method_code": "no-shipping-required",
            "shipping_charge": {"currency": "EUR", "excl_tax": "0.00", "tax": "0.00"},
            "shipping_address": {
                "country": "http://127.0.0.1:8000/api/countries/NL/",
                "first_name": "Henk",
                "last_name": "Van den Heuvel",
                "line1": "Roemerlaan 44",
                "line2": "",
                "line3": "",
                "line4": "Kroekingen",
                "notes": "Niet STUK MAKEN OK!!!!",
                "phone_number": "+31 26 370 4887",
                "postcode": "7777KK",
                "state": "Gerendrecht",
                "title": "Mr",
            },
        }

    def test_checkout_serializer_validation(self):
        self.login(username="nobody", password="nobody")

        # first create a basket and a checkout payload
        response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        basket = response.data
        payload = self._get_common_payload(basket["url"])

        # create a request and user for the serializer
        rf = RequestFactory()
        request = rf.post("/checkout", **payload)
        request.user = User.objects.get(username="nobody")

        serializer = CheckoutSerializer(data=payload, context={"request": request})
        self.assertTrue(serializer.is_valid())
        # see https://github.com/django-oscar/django-oscar-api/issues/188
        self.assertEqual(serializer.validated_data["total"], Decimal("50.00"))

    def test_checkout(self):
        """Test if an order can be placed as an authenticated user with session based auth."""
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)
        basket = response.data

        payload = self._get_common_payload(basket["url"])
        response = self.post("api-checkout", **payload)
        self.assertEqual(response.status_code, 406)
        response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.assertEqual(response.status_code, 200)
        response = self.post("api-checkout", **payload)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["email"],
            "nobody@nobody.niks",
        )
        self.assertEqual(
            Basket.objects.get(pk=basket["id"]).status,
            "Frozen",
            "Basket should be frozen after placing order and before payment",
        )

    def test_checkout_header(self):
        """Prove that the user 'nobody' can checkout his cart when authenticating with header session."""
        self.hlogin("nobody", "nobody", session_id="nobody")
        response = self.get("api-basket", session_id="nobody", authenticated=True)
        self.assertTrue(response.status_code, 200)
        basket = response.data

        payload = self._get_common_payload(basket["url"])
        response = self.post(
            "api-checkout", session_id="nobody", authenticated=True, **payload
        )
        self.assertEqual(response.status_code, 406)
        response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
            session_id="nobody",
            authenticated=True,
        )
        self.assertEqual(response.status_code, 200)
        response = self.post(
            "api-checkout", session_id="nobody", authenticated=True, **payload
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["email"],
            "nobody@nobody.niks",
        )
        self.assertEqual(
            Basket.objects.get(pk=basket["id"]).status,
            "Frozen",
            "Basket should be frozen after placing order and before payment",
        )

    def test_checkout_implicit_shipping(self):
        """Test if an order can be placed without specifying shipping method."""
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)
        basket = response.data

        payload = self._get_common_payload(basket["url"])
        del payload["shipping_method_code"]
        del payload["shipping_charge"]

        response = self.post("api-checkout", **payload)
        self.assertEqual(response.status_code, 406)
        response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.assertEqual(response.status_code, 200)
        response = self.post("api-checkout", **payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Basket.objects.get(pk=basket["id"]).status,
            "Frozen",
            "Basket should be frozen after placing order and before payment",
        )

    def test_checkout_billing_address(self):
        """Test if an order can be placed with a billing address."""
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)
        basket = response.data

        payload = self._get_common_payload(basket["url"])
        payload["billing_address"] = {
            "country": "http://127.0.0.1:8000/api/countries/NL/",
            "first_name": "Jos",
            "last_name": "Henken",
            "line1": "Stationstraat 4",
            "line2": "",
            "line3": "",
            "line4": "Hengelo",
            "notes": "",
            "phone_number": "+31 26 370 1111",
            "postcode": "1234AA",
            "state": "Gelderland",
            "title": "Mr",
        }

        self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        response = self.post("api-checkout", **payload)
        self.assertEqual(response.status_code, 200)

    def test_checkout_wrong_billing_address(self):
        """Prove that an order cannot be placed with invalid billing address."""
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)
        basket = response.data

        payload = self._get_common_payload(basket["url"])
        payload["billing_address"] = {"country": "This is wrong"}

        self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        response = self.post("api-checkout", **payload)
        # It should complain about the billing address
        self.assertEqual(response.status_code, 406)
        self.assertEqual(
            response.data["billing_address"]["country"][0],
            "Invalid hyperlink - No URL match.",
        )

    def test_client_cannot_falsify_total_price(self):
        """Prove that the total price variable sent along with a checkout request, can not be manipulated."""
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)
        basket = response.data

        payload = self._get_common_payload(basket["url"])
        payload["total"] = "150.00"  # Instead of '50.00'

        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.response.assertStatusEqual(200)
        self.response = self.post("api-checkout", **payload)
        self.response.assertStatusEqual(406)
        self.response.assertValueEqual(
            "non_field_errors", ["Total incorrect 150.00 != 50.00"]
        )

    def test_client_cannot_falsify_shipping_charge(self):
        """Prove that the shipping charge variable sent along with a checkout request, can not be manipulated."""
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)
        basket = response.data

        payload = self._get_common_payload(basket["url"])
        payload["shipping_charge"]["excl_tax"] = "42.00"  # Instead of '0.00'

        response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.assertEqual(response.status_code, 200)
        response = self.post("api-checkout", **payload)
        self.assertEqual(response.status_code, 406, response.data)
        error_message = response.data["non_field_errors"][0]
        self.assertIn("Shipping price incorrect", error_message)

    def test_utf8_encoding(self):
        """We should accept utf-8 (non ascii) characters in the address."""
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)
        basket = response.data

        payload = self._get_common_payload(basket["url"])
        payload["shipping_address"]["line1"] = "Ї ❤ chǼractɇɌȘ"

        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.response.assertStatusEqual(200)
        self.response = self.post("api-checkout", **payload)
        self.response.assertStatusEqual(200)
        self.assertEqual(
            self.response.data["shipping_address"]["line1"], u"Ї ❤ chǼractɇɌȘ"
        )

    def test_checkout_empty_basket(self):
        """When basket is empty, checkout should raise an error."""
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)
        basket = response.data

        response = self.get(basket["lines"])
        self.assertTrue(response.status_code, 200)
        lines = response.data

        self.assertEqual(lines, [])

        payload = self._get_common_payload(basket.get("url"))
        self.response = self.post("api-checkout", **payload)
        self.response.assertStatusEqual(406)
        self.response.assertValueEqual(
            "non_field_errors", ["Cannot checkout with empty basket"]
        )

    def test_total_is_optional(self):
        """Total should be an optional value."""
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)
        basket = response.data

        payload = self._get_common_payload(basket["url"])
        del payload["total"]

        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.response.assertStatusEqual(200)
        self.response = self.post("api-checkout", **payload)
        self.response.assertStatusEqual(200)

    def test_can_login_with_frozen_user_basket(self):
        """When a user has an unpaid order, he should still be able to log in."""
        self.test_checkout()
        self.delete("api-login")
        self.get("api-basket")
        self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.response = self.post("api-login", username="nobody", password="nobody")
        self.response.assertStatusEqual(200)
        self.login(username="nobody", password="nobody")

    def test_anonymous_checkout(self):
        """Test if an order can be placed as an anonymous user."""
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)
        basket = response.data

        payload = self._get_common_payload(basket["url"])
        del payload["guest_email"]

        with self.settings(OSCAR_ALLOW_ANON_CHECKOUT=True):
            response = self.post("api-checkout", **payload)
            self.assertEqual(response.status_code, 406)
            response = self.post(
                "api-basket-add-product",
                url="http://testserver/api/products/1/",
                quantity=5,
            )
            self.assertEqual(response.status_code, 200)

            # No guest email specified should say 406
            response = self.post("api-checkout", **payload)
            self.assertEqual(response.status_code, 406)

            # An empty email address should say this as well
            payload["guest_email"] = ""
            response = self.post("api-checkout", **payload)
            self.assertEqual(response.status_code, 406)

            # Add in guest_email to get a 200
            payload["guest_email"] = "henk@example.com"
            response = self.post("api-checkout", **payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["email"], "henk@example.com")
            self.assertEqual(
                Basket.objects.get(pk=basket["id"]).status,
                "Frozen",
                "Basket should be frozen after placing order and before payment",
            )

    def test_checkout_creates_an_order(self):
        """After checkout has been done, a user should have gained an order object."""
        # first create an anonymous order
        self.test_anonymous_checkout()

        # and now an order for the user nobody
        self.login(username="nobody", password="nobody")
        self.test_checkout()
        self.response = self.get("order-list")
        # the anonymous order should not be listed
        self.assertEqual(len(self.response), 1, "An order should have been created.")

        order_url = self.response.data[0]["url"]
        self.response = self.get(order_url)
        orderlines_url = self.response["lines"]
        self.response = self.get(orderlines_url)
        self.assertEqual(len(self.response), 1, "The order should have one orderline.")

        orderline_url = self.response.data[0]["url"]
        self.response = self.get(orderline_url)

        self.assertEqual(
            self.response["order"],
            order_url,
            "the order url from a line is the same as the one created",
        )

    def test_order_api_surcharges(self):
        """Surcharges should be shown in the API when they are applied"""
        # and now an order for the user nobody
        self.login(username="nobody", password="nobody")
        self.test_checkout()
        self.response = self.get("order-list")
        self.assertEqual(len(self.response), 1, "An order should have been created.")

        order_url = self.response.data[0]["url"]
        order = Order.objects.get(number=self.response.data[0]["number"])
        order.surcharges.create(
            name="Surcharge", code="surcharge", excl_tax=10.00, incl_tax=10.00
        )

        self.response = self.get(order_url)
        self.assertEqual(
            len(self.response["surcharges"]), 1, "The order should have one surcharge."
        )
        self.assertEqual(self.response["surcharges"][0]["code"], "surcharge")
        self.assertEqual(self.response["surcharges"][0]["name"], "Surcharge")
        self.assertEqual(self.response["surcharges"][0]["excl_tax"], "10.00")
        self.assertEqual(self.response["surcharges"][0]["incl_tax"], "10.00")

    @patch("oscarapi.signals.oscarapi_post_checkout.send")
    def test_post_checkout_signal_send(self, mock):
        """The `oscarapi_post_checkout` signal should be send after checkout."""
        self.test_anonymous_checkout()
        self.assertTrue(mock.called)
        # Make sure it's a django Response instance and not the DRF module
        self.assertTrue(isinstance(mock.call_args[1]["response"], Response))

    def test_checkout_permissions(self):
        """Prove that someone cannot check out someone else's cart by mistake."""
        # First login as nobody
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")

        # Store this basket because somebody is going to checkout with this
        basket = response.data
        nobody_basket_url = basket.get("url")

        self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )

        self.client.logout()

        # Now login as somebody and fill another basket
        self.login(username="somebody", password="somebody")
        self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )

        # So let's checkout with nobody's basket WHAHAAAHAHA!
        payload = self._get_common_payload(nobody_basket_url)

        # Oh, this is indeed not possible
        response = self.post("api-checkout", **payload)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, "Unauthorized")

    def test_shipping_methods(self):
        """Test if shipping methods can be fetched for baskets."""
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)

        payload = self._get_common_payload(None)["shipping_address"]
        self.response = self.post("api-basket-shipping-methods", **payload)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response), 1)
        self.assertDictEqual(
            self.response[0],
            {
                "code": "no-shipping-required",
                "name": "No shipping required",
                "description": "",
                "is_discounted": False,
                "discount": 0,
                "price": {
                    "currency": None,
                    "excl_tax": "0.00",
                    "incl_tax": "0.00",
                    "tax": "0.00",
                },
            },
        )
        response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.assertEqual(response.status_code, 200)

        self.response = self.post("api-basket-shipping-methods", **payload)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response), 1)
        self.assertDictEqual(
            self.response[0],
            {
                "code": "free-shipping",
                "name": "Free shipping",
                "description": "",
                "is_discounted": False,
                "discount": 0,
                "price": {
                    "currency": "EUR",
                    "excl_tax": "0.00",
                    "incl_tax": "0.00",
                    "tax": "0.00",
                },
            },
        )

    def test_cart_immutable_after_checkout(self):
        """Prove that the cart can not be changed after checkout."""
        self.login(username="nobody", password="nobody")
        response = self.get("api-basket")
        self.assertTrue(response.status_code, 200)
        basket = response.data

        payload = self._get_common_payload(basket["url"])
        self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.post("api-checkout", **payload)
        self.assertEqual(
            Basket.objects.get(pk=basket["id"]).status,
            "Frozen",
            "Basket should be frozen after placing order and before payment",
        )

        url = reverse("basket-detail", args=(basket["id"],))
        response = self.get(url)
        self.assertEqual(response.status_code, 404)  # Frozen basket can not be accessed
