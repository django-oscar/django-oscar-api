from django.utils import timezone

from oscar.core.loading import get_model

from oscarapi.tests.utils import APITest


Basket = get_model("basket", "Basket")
ConditionalOffer = get_model("offer", "ConditionalOffer")
Voucher = get_model("voucher", "Voucher")


class VoucherTest(APITest):
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
        "voucher",
    ]

    def setUp(self):
        # Adjust offer dates so it's valid
        offer = ConditionalOffer.objects.get(name="Offer for voucher 'testvoucher'")
        offer.start_datetime = timezone.now()
        offer.end_datetime = timezone.now() + timezone.timedelta(days=1)
        offer.save()

        # adjust voucher dates for testing the view
        voucher = Voucher.objects.get(name="testvoucher")
        voucher.start_datetime = timezone.now()
        voucher.end_datetime = timezone.now() + timezone.timedelta(days=1)
        voucher.save()

        super(VoucherTest, self).setUp()

    def test_basket_add_voucher(self):
        """Check if we can add a voucher with the add-voucher api call"""
        # first add two products to our basket
        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=2,
        )
        self.response.assertStatusEqual(200)

        # total should be 20
        self.response = self.get("api-basket")
        self.response.assertValueEqual("total_incl_tax", "20.00")

        # add a voucher and see if the voucher is added correctly
        self.response = self.post("api-basket-add-voucher", vouchercode="TESTVOUCHER")
        self.response.assertStatusEqual(200)

        # see if the discount of 5.00 from the voucher was applied
        self.response = self.get("api-basket")
        self.response.assertValueEqual("total_incl_tax", "15.00")

    def test_lowercase_voucher(self):
        """Lowercase vouchers should be working as well"""
        # first add two products to our basket
        self.response = self.post(
            "api-basket-add-product",
            url="http://testserver/api/products/1/",
            quantity=2,
        )
        self.response.assertStatusEqual(200)

        self.response = self.post("api-basket-add-voucher", vouchercode="testvoucher")
        self.response.assertStatusEqual(200)
