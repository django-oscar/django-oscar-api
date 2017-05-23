=========
Changelog
=========

1.1.3 (2017-05-23)
-------------------
Features:
  * Updated documentation to mention the django-oscar-api-checkout plugin

Fixes:
  * #100 The checkout view should not use the wrong mixin to check the basket ownership

1.1.2 (2017-05-10)
-------------------
Fixes:
  * #98 Fix user address integrity error

1.1.1 (2017-05-09)
-------------------
Features:
  * #97 Now it's possible to manage your address book (user addresses)

Fixes:
  * #95 basket/shipping-methods could use another basket (aleksandrpanteleymonov)
  * Fixed sandbox settings to work with Django 1.10
  * Updated docs to use new urlpatterns format


1.1.0 (2017-03-13)
-------------------
Features:
  * #88 Checkout with a billing address is now supported
  * Drops support for Django 1.7, tested with Oscar 1.4

Fixes:
  * Updated requirements: `djangorestframework>=3.3`

1.0.10 (2016-12-08)
-------------------
Fixes:
  * #82 Recalculate offers when updating lines or receiving them individually
  * Make sure that the `post` and `delete` methods of the LoginView return valid (json) responses
  * #86 Add missing Meta.fields attribute to work the default first level of api endpoints. (jklapuch)

Features:
  * Updated the documentation and added a demosite to explain how to override a view/serializer

1.0.9 (2016-10-24)
------------------
Fixes:
  * RestFramework will nolonger complain about "Creating a ModelSerializer
    without either the 'fields' attribute or the 'exclude' attribute has been
    deprecated since 3.3.0, and is now disallowed. Add an explicit
    fields = '__all__' to the LineAttributeSerializer serializer."

1.0.8 (2016-10-04)
------------------
Fixes:
  * #78 PUT on BasketLineSerializer was raising a 500 error due to incorrect LineAttributeSerializer definition

1.0.7 (2016-08-26)
------------------
Fixes:
  * #77 Use configured LoginSerializer instead of the hardcoded one (whyscream)
  * Cleaned up urls.py to be compatible with django 1.10 (SalahAdDin)

1.0.6 (2016-07-27)
------------------
Features:
  * Make `add_voucher` a class based view so we can easily override the serializer

Fixes:
  * Oscar expects 'vouchercode' to be uppercase
  * #74 Python 3 does not have `itertools.imap`, we use `six.moves.map` now (crgwbr)

1.0.5 (2016-07-13)
------------------

Fixes:
  * #70 Change process_response to have acorrect  API created basket cookie added to the response (albertojacini)

1.0.4 (2016-04-04)
------------------

Features:
  * #65 Add Docker configuration for testing convenience (crgwbr) 

Fixes:
  * #66 Raise a ValidationError (instead of a 500 server error)  when you try to checkout with an empty basket (crgwbr)
  * #67 Fixes an AssertionError in the LineList view (missing queryset attribute)

1.0.3 (2016-03-21)
------------------

Features:
  * #35 Changes format of urls of basket lines (lines/1 -> basket/1/lines/1) 
  * #63 Make AddProductSerializer easily overridable

Fixes:
  * #63 You can now update basketlines more easily with a PUT, updated documentation for this

1.0.2 (2016-03-01)
------------------
Features:
  * #58 Send a signal after placing an order so you don't need to customize the CheckoutView for custom post actions (bufke)

Fixes:
  * #60 ``is_quantity_allowed`` returned the quantity and not an error message (bootinge)
  * Updated the docs with forgotten application definition (SamuelSilveira)

1.0.1 (2016-01-29)
------------------
Fixes:
  * #57 Make sure that we are really compatible with Django 1.9 (against Oscar Dev)
  * Removed `django-compressor<2.0` as a dependency
  * Fix for the `LoginSerializer` to make it work with custom username fields

1.0.0 (2016-01-14)
------------------
Initial release.
