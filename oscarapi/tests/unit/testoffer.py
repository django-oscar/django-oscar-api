from oscar.core.loading import get_model

from oscarapi.tests.utils import APITest


Basket = get_model("basket", "Basket")


class OfferTest(APITest):
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
        "offer",
    ]

    def test_basket_discount(self):
        "A discount should be properly applied to the basket total"
        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=5,
        )
        self.response.assertStatusEqual(200)

        self.response.assertValueEqual("total_excl_tax", "42.00")
        self.response.assertValueEqual("total_incl_tax", "42.00")
        self.response.assertValueEqual("total_excl_tax_excl_discounts", "50.00")
        self.response.assertValueEqual("total_incl_tax_excl_discounts", "50.00")

    def test_basket_line_discount(self):
        "A discount should be properly applied to the basket line"
        self.test_basket_discount()
        self.response = self.get(self.response["lines"])
        self.assertEqual(len(self.response.body), 1)
        line0 = self.response.body[0]
        self.assertEqual(line0["product"], "http://testserver/api/products/1/")
        self.assertEqual(line0["quantity"], 5)
        self.assertEqual(line0["price_excl_tax"], "42.00")
        self.assertEqual(line0["price_incl_tax"], "42.00")
        self.assertEqual(line0["price_excl_tax_excl_discounts"], "50.00")
        self.assertEqual(line0["price_incl_tax_excl_discounts"], "50.00")

        # check if the discount is applied when we retrieve a single line
        self.response = self.get(self.response.body[0]["url"])
        single_line0 = self.response.body
        self.assertEqual(single_line0["price_excl_tax"], "42.00")
        self.assertEqual(single_line0["price_incl_tax"], "42.00")
        self.assertEqual(single_line0["price_excl_tax_excl_discounts"], "50.00")
        self.assertEqual(single_line0["price_incl_tax_excl_discounts"], "50.00")

    def test_adjust_line_quantity_discount(self):
        "A single line response should return the price including the discount"
        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=1,
        )
        self.response.assertStatusEqual(200)

        # Get the basket lines, and update the quantity to 2
        self.response = self.get("api-basket")
        self.response = self.get(self.response["lines"])
        basket_line_url = self.response.data[0]["url"]
        self.response = self.patch(basket_line_url, quantity=2)
        self.response.assertStatusEqual(200)

        # this price is excl discount
        self.assertEqual(self.response["price_incl_tax_excl_discounts"], "20.00")
        # this price should be incl discount
        self.assertEqual(self.response["price_incl_tax"], "12.00")
        self.assertEqual(self.response["price_excl_tax"], "12.00")
