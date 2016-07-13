================
Django Oscar API
================

This package provides a RESTful API for `django-oscar`_.

.. _`django-oscar`: https://github.com/django-oscar/django-oscar

.. image:: https://travis-ci.org/django-oscar/django-oscar-api.svg?branch=master
    :target: https://travis-ci.org/django-oscar/django-oscar-api

.. image:: http://codecov.io/github/django-oscar/django-oscar-api/coverage.svg?branch=master 
    :alt: Coverage
    :target: http://codecov.io/github/django-oscar/django-oscar-api?branch=master

.. image:: https://readthedocs.org/projects/django-oscar-api/badge/
   :alt: Documentation Status
   :target: https://django-oscar-api.readthedocs.io/

.. image:: https://img.shields.io/pypi/v/django-oscar-api.svg
   :alt: Latest PyPi release
   :target: https://pypi.python.org/pypi/django-oscar-api

.. image:: https://img.shields.io/badge/koe-15-brightgreen.svg
   :alt: How many times koe is in the sourcecode
   :target: https://github.com/django-oscar/django-oscar-api/blob/master/oscarapi/tests/testlogin.py#L23

Usage
=====

To use the Oscar API application in an Oscar E-commerce site, follow these
steps:

1. Install the `django-oscar-api` package someway (``pip install django-oscar-api``).
2. Add oscarapi to INSTALLED_APPS.
3. Add the application's urls to your urlconf::
    
    from oscarapi.app import application as api
    urlpatterns = patterns('',
        # all the things you allready got
        url(r'^api/', include(api.urls)),
    )

See the Documentation_ for more information.

.. _Documentation: https://django-oscar-api.readthedocs.io

Changelog
=========

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


