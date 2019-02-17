============================
Use Oscar API out-of-the-box
============================

To use the oscarapi application in an oscar ecommerce site without overriding or customizing the default views and serializers just follow these steps:

1. Install it (see :ref:`django-oscar-api-installation`)
2. Add ``rest_framework`` and ``oscarapi`` to your INSTALLED_APPS section in ``settings.py``
3. Add the application's urls to your own app's `url.py`:

.. code-block:: python

    from oscarapi.app import application as api
    urlpatterns = [
        # ... all the things you allready got
        
        # for django version < 2.0 use ... 
        url(r'^api/', api.urls),
        # OR
        # for django version >= 2.0 use ... 
        re_path(r'^api/', api.urls), 
    ]

.. _mixed-usage-label:

4. And then perform migration for django oscar app:
.. code-block:: python

    python manage.py migrate

Middleware and mixed usage
--------------------------

There are some middleware classes shipped with Oscar API which can be useful for your project. For example, we have seen in practice that it can be useful to mix plain Oscar and the API (fill your basket with the API and use plain Oscar views for checkout).

See the :doc:`/usage/middleware` section for more information.


