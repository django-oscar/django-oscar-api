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

.. image:: https://badge.fury.io/py/django-oscar-api.svg
   :alt: Latest PyPi release
   :target: https://pypi.python.org/pypi/django-oscar-api

.. image:: https://img.shields.io/badge/koe-18-brightgreen.svg
   :alt: How many times koe is in the sourcecode
   :target: https://github.com/django-oscar/django-oscar-api/blob/master/oscarapi/tests/testlogin.py#L23

Usage
=====

To use the Oscar API application in an Oscar E-commerce site, follow these
steps:

1. Install the `django-oscar-api` package (``pip install django-oscar-api``).
2. Add oscarapi to INSTALLED_APPS.
3. Add the application's urls to your urlconf::
    
    from oscarapi.app import application as api

    urlpatterns = (
        # all the things you already have
        url(r'^api/', api.urls),
    )

See the Documentation_ for more information and the Changelog_ for release notes.

.. _Documentation: https://django-oscar-api.readthedocs.io
.. _Changelog: https://django-oscar-api.readthedocs.io/en/latest/changelog.html

