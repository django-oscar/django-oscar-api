=========
Changelog
=========

1.5.1 (2018-10-01)
------------------
Fixes:
  * #134 Fixed issue in post checkout signal: Make sure we send the response instance, and not the DRF module

1.5.0 (2018-10-01)
------------------
Features:
  * #134 It's now possible to update basket line attribute options (eg color)
  * #135 Tested with Python 3.7

Fixes:
  * #133 Fix for Python 3 compatibility in the Api Gateway Middleware (akutsuacts)

Notes:
  Dropped the ``IsAdminUserOrRequestContainsBasket`` and ``IsAdminUserOrRequestContainsLine`` permissions, they are
  replaced with the ``IsAdminUserOrRequestAllowsAccessTo`` permission. Please check your customised views if
  you have overridden the ``permissions`` attribute or added your own custom permissions.

1.4.1 (2018-08-17)
------------------
Features:
  * #128 Improved shipping method API: It's now possible to check shipping options when shipping address is known

Fixes:
  * #127 Fix for Python 3 compatibility (fquinner)


1.4.0 (2018-05-29)
------------------
Features:
 * #124 Drops support for Django 1.8, added support for Django 2.0, added support for Oscar 1.6

Notes:
  Dropped support for Django < 1.11

1.3.1 (2018-04-24)
------------------
Features:
  * #118 Added ``code`` field in the ``ProductAttributeValueSerializer``.
  * #119 Default add ``upc`` to the ``ProductSerializer``

Fixes:
  * Added app_label to the `ApiKey` model so you don't need to have `oscarapi` in INSTALLED_APPS when using oscarapi middleware classes (when you don't need oscarapi specific models).

Notes:
  Dropped support for Django 1.10.x.


1.3.0 (2018-01-16)
------------------
Features:
  * Better support for the different ProductAttribute types in the serializer (including Entity when you implement a `.json()` method on your model)
  * Added a filter to the ProductList view so you can query standalone/parent/child products (for example http://127.0.0.1:8000/api/products/?structure=standalone)
  * The Product list and Product detail views use the same serializer now

Fixes:
  * Added app_label to the `ApiKey` model so you don't need to have `oscarapi` in INSTALLED_APPS when using oscarapi middleware classes (when you don't need oscarapi specific models).

Notes:
  Dropped support for Oscar versions < 1.5 (as we support new features which are available since oscar 1.5)

1.2.1 (2017-12-15)
-------------------
Fixes:
  * Shipping address is not required during checkout

Features:
  * Tested with Oscar 1.5.1, updated dependencies

1.2.0 (2017-11-06)
-------------------
Features:
  * #109 Added support for Django 1.11 and Oscar 1.5. See the installation documentation for instructions. (whyscream)

1.1.5 (2017-09-12)
-------------------
Fixes:
  * #105 `ProductPrice` and `ProductAvailability` views resuled in server error if the matching product is not found (taaviteska)

1.1.4 (2017-07-04)
-------------------
Features:
  * #102 Let the `ProductAttribute` and `ProductAttributeValue` serializer fields be overridable in the settings (yazanhorani)
  * #101 Don't delete anonymous basket which are merged after login, leave them in the database with the status ``MERGED`` (aleksandrpanteleymonov)

Notes:
  Before this release, anonymous baskets where merged in the ``LoginView`` and after being merged, deleted. This behaviour is now removed, so anonymous baskets remain in the database and have the status ``MERGED`` (This is more in the direction of how Oscar is working). You can change this behaviour by overriding the ``merge_baskets`` method / hook in the ``LoginView``, or you should add a cron job to cleanup old baskets with the status ``MERGED`` from the database.


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
  * #70 Change process_response to have a correct API created basket cookie added to the response (albertojacini)

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
