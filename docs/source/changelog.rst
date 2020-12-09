=========
Changelog
=========
2.1.1 (2020-12-09)
------------------
A minor bugfix release to fix a typo in the `RegisterUserSerializer` definition.

Fixed:
 * `#255 <https://github.com/django-oscar/django-oscar-api/pull/255>`_ Fix misspelled serializer name (farooqaaa)


2.1.0 (2020-11-13)
------------------
This release adds support for Oscar 2.1 and includes various new features and fixes. Supported Django versions are 2.2 and 3.0, and supported Python versions are 3.6, 3.7 and 3.8.

Features:
 * `#202 <https://github.com/django-oscar/django-oscar-api/pull/202>`_ Defer downloading of image data until the file data is accessed
 * `#219 <https://github.com/django-oscar/django-oscar-api/pull/219>`_ Allow DRF Versioning schemes. You need to accept ``*args`` and ``**kwargs`` in your view overrides.
 * `#238 <https://github.com/django-oscar/django-oscar-api/pull/239>`_ The Order serializer replaced the ``guest_email`` with an ``email`` field which is used for both anonymous and user associated orders (viggo-devries)
 * `#244 <https://github.com/django-oscar/django-oscar-api/pull/244>`_ Added separate User serializers for the regular and admin API, introduced the ``OSCARAPI_EXPOSE_USER_DETAILS`` setting to control the exposure of user details
 * `#246 <https://github.com/django-oscar/django-oscar-api/pull/246>`_ Added a user registration endpoint. It can be enabled/disabled with the ``OSCARAPI_ENABLE_REGISTRATION`` setting
 * `#251 <https://github.com/django-oscar/django-oscar-api/pull/251>`_ Also serialize ``Surcharge`` objects in the Order serializer (Surcharges are introduced in Oscar 2.1)

Fixed:
 * `#213 <https://github.com/django-oscar/django-oscar-api/pull/213>`_ Fix OpenAPI integration (mazur-work)
 * `#221 <https://github.com/django-oscar/django-oscar-api/pull/221>`_ Fix APIGatewayMiddleware handling of valid API keys (solarissmoke)
 * `#228 <https://github.com/django-oscar/django-oscar-api/pull/228>`_ BasketLineDetail: Use DRF get_object_or_404 (jayvdb)
 * `#230 <https://github.com/django-oscar/django-oscar-api/pull/230>`_ Mount the Admin API on the /admin endpoint with ``path()``
 * `#234 <https://github.com/django-oscar/django-oscar-api/pull/234>`_ Make all Admin API url endpoints prefixed consistently with ``admin-``


2.0.2 (2019-12-20)
------------------
This is a bugfix release for version 2.0.1.

Fixed:
 * `#207 <https://github.com/django-oscar/django-oscar-api/pull/207>`_ Added a sane and clear error message when construct_id_filter does not construct a useful filter.


2.0.1 (2019-11-22)
------------------
This is a bugfix release for version 2.0.0.

Fixed:
 * `#187 <https://github.com/django-oscar/django-oscar-api/pull/187>`_ Have more informative validation errors when using the ``AttributeValueField``
 * `#190 <https://github.com/django-oscar/django-oscar-api/pull/190>`_ Fix broken ``Orderline`` Admin API view, improved ``BasketView`` queryset
 * `#191 <https://github.com/django-oscar/django-oscar-api/pull/191>`_ Fix quantity validation in ``AddProductView`` (laevilgenius)
 * `#194 <https://github.com/django-oscar/django-oscar-api/pull/194>`_ Do not change the "total" field type from Decimal to Price in the ``CheckouSerializer``
 * `#195 <https://github.com/django-oscar/django-oscar-api/pull/195>`_ Fix broken API views when the Admin API is disabled. This adds a new ``StockRecord`` view for products
 * `#197 <https://github.com/django-oscar/django-oscar-api/pull/197>`_ Fix typos in README (Patil2099)
 * `#198 <https://github.com/django-oscar/django-oscar-api/pull/198>`_ Fix unused imports and typos (Samitnuk)


2.0.0 (2019-09-09)
-------------------
Features:
 * `#156 <https://github.com/django-oscar/django-oscar-api/pull/156>`_ Added Oscar 2.0 compatibility, see notes below
 * `#185 <https://github.com/django-oscar/django-oscar-api/pull/185>`_ Added a hook to implement a custom entity value handler

This release adds Oscar 2.0 support. This release is not backwards compatible with Oscar 1.6.x and below and requires code changes.

Noticeable changes:
 - This release drops support for Oscar < 2.0
 - This release drops support for python 2.7 and requires python >= 3.5
 - This release drops support for Django 1.11 and requires Django 2.1.x or 2.2.x
 - This release drops support for Django Rest Framework < 3.9
 - `PutIsPatchMixin` has been removed, so `PUT` and `PATCH` act like they should
 - Removed the `RESTApiApplication` Oscar app and added an `OscarAPIConfig` Django AppConfig


1.6.2 (2019-08-26)
-------------------
Fixed:
 * `#182 <https://github.com/django-oscar/django-oscar-api/pull/182>`_ Fix error when ``OSCARAPI_BLOCK_ADMIN_API_ACCESS`` is not defined in settings
 * `#183 <https://github.com/django-oscar/django-oscar-api/pull/183>`_ Removed unused ``Meta`` class from ``AdductSerializer`` (samitnuk)

Features:
 * `#180 <https://github.com/django-oscar/django-oscar-api/pull/180>`_ Improved Products Admin API: Allow PUT and PATCH without specifying ID
 * `#181 <https://github.com/django-oscar/django-oscar-api/pull/181>`_ Improved Categories Admin API: Create categories from full slug (StefanJilsink)


1.6.1 (2019-06-27)
-------------------
Fixed:
 * `#176 <https://github.com/django-oscar/django-oscar-api/pull/176>`_ Fixed an issue where Child Products could not be updated with the Admin API
 * `#179 <https://github.com/django-oscar/django-oscar-api/pull/179>`_ Make sure we don't use the ``.is_staff`` check anymore anywhere. This is now completely replaced with the *Admin API*
 * `#179 <https://github.com/django-oscar/django-oscar-api/pull/179>`_ Removed any functionality to create (``POST``) new baskets in the ``BasketList`` view. If any need of this exists, this should be implemented in the *Admin API*
 * `#179 <https://github.com/django-oscar/django-oscar-api/pull/179>`_ Staff users are now allowed to login and do a regular checkout

Features:
 * `#173 <https://github.com/django-oscar/django-oscar-api/pull/173>`_ Added missing checkout tests (samitnuk)
 * `#178 <https://github.com/django-oscar/django-oscar-api/pull/178>`_ Send the basket addition signal in the ``AddProductView``
 * `#179 <https://github.com/django-oscar/django-oscar-api/pull/179>`_ Check for the ``OSCARAPI_BLOCK_ADMIN_API_ACCESS`` setting to expose the *Admin API* at all. Useful for production websites where you completely want to disable this. Updated documentation for this

1.6.0 (2019-06-13)
-------------------
This release is primary focussed on (some long desired) new features. This will also be the last release which is compatible with django-oscar 1.5.x and 1.6.x and django 1.11/2.1. The next release, 2.0,  will be compatible with django-oscar 2.0.

Fixed:
 * Include setup.py when creating a source dist
 * `#165 <https://github.com/django-oscar/django-oscar-api/pull/165>`_ Only open baskets should be merged (dipen30)
 * `#168 <https://github.com/django-oscar/django-oscar-api/pull/168>`_ Serializers consistency improvements (samitnuk)

Features:
 * `#157 <https://github.com/django-oscar/django-oscar-api/pull/157>`_ introduced ``get_api_class`` and ``get_api_classes`` for easier customisation of Oscar API. See the `Updated documentation <https://django-oscar-api.readthedocs.io/en/latest/topics/customizing_oscarapi.html>`_ about this topic.
 * `#158 <https://github.com/django-oscar/django-oscar-api/pull/158>`_ introduced the *Admin API* which makes it possible to manage Oscar entities via the API. Think of Product / Productclass / Category creation and managing. See the `Admin API documentation <https://django-oscar-api.readthedocs.io/en/latest/topics/the_admin_api.html>`_ about this topic.

Some noticable features and changes of `#158 <https://github.com/django-oscar/django-oscar-api/pull/158>`_:
 * `#126 <https://github.com/django-oscar/django-oscar-api/pull/126>`_ Added a *Category API*
 * `#154 <https://github.com/django-oscar/django-oscar-api/issues/154>`_ Added a *Order Admin API*
 * Removed the ``IsAdminUserOrRequestAllowsAccessTo`` and ``HasUser`` permissions and added the ``RequestAllowsAccessTo`` and ``APIAdminPermission`` permissions and applied them to the corresponding views.
 * Removed the ``LineList`` and ``LineaAtributes`` list API's
 * Removed the ``StockRecordList`` API
 * Moved the ``PartnerList`` API to the *Admin API* and added the correct permission
 * Moved the ``UserList`` API to the *Admin API* and added the correct permission
 * Fixed several wrong usages of ``PutIsPatchMixin``

1.5.4 (2019-03-05)
------------------
Fixed:
  * #151 Keep the ``tests/utils.py`` file in the distribution

1.5.3 (2019-02-19)
------------------
Fixed:
  * #144 Don't distribute the sandbox package

Features:
  * Also released a a universal wheel now.

1.5.2 (2018-11-22)
------------------
Fixed:
  * #140 Changed wrong exception type in HeaderSessionMiddleware from NotAcceptable to PermissionDenied (whyscream)

1.5.1 (2018-10-01)
------------------
Fixes:
  * #136 Fixed issue in post checkout signal: Make sure we send the response instance, and not the DRF module

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
