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
   :target: http://django-oscar-api.readthedocs.org/


Usage
=====

To use the oscarapi application in an oscar ecommerce site, follow these
steps:

1. Install the `django-oscar-api` package someway (``pip install django-oscar-api``).
2. Add oscarapi to INSTALLED_APPS.
3. Add the application's urls to your urlconf::
    
    from oscarapi.app import application as api
    urlpatterns = patterns('',
        # all the things you allready got
        url(r'^api/', include(api.urls)),
    )

See `readthedocs`_ for more information.

.. _`readthedocs`: https://django-oscar-api.readthedocs.org

