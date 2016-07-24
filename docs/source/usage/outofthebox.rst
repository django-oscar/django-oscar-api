============================
Use Oscar API out-of-the-box
============================

To use the oscarapi application in an oscar ecommerce site without overriding or customizing the default views and serializers just follow these steps:

1. Install it (see :ref:`django-oscar-api-installation`)
2. Add ``rest_framework`` and ``oscarapi`` to your INSTALLED_APPS section in ``settings.py``
3. Add the application's urls to your own app's `url.py`:

.. code-block:: python

    from oscarapi.app import application as api
    urlpatterns = patterns('',
        # ... all the things you allready got
        url(r'^api/', include(api.urls)),
    )

.. _mixed-usage-label:

Middleware and mixed usage
--------------------------

There are some middleware classes shipped with Oscar API which can be useful for your project. For example, we have seen in practise that it can be useful to mix plain Oscar and the API (fill your basket with the API and use plain Oscar views for checkout).

See the :doc:`/usage/middleware` section for more information.


