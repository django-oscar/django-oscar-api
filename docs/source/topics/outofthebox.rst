============================
Use Oscar API out-of-the-box
============================

To use the oscarapi application in an oscar ecommerce site without overriding or customizing the default views and serializers just follow these steps:

1. Install it (see :ref:`django-oscar-api-installation`)
2. Add ``rest_framework`` and ``oscarapi`` to your INSTALLED_APPS section in ``settings.py``
3. Add the application's urls to your urlconf

   .. code-block:: python

      from django.urls import include

      urlpatterns = (
          # all the things you already have
          path("api/", include("oscarapi.urls")),
      )

4. Apply migrations::

    python manage.py migrate

.. note::
    It's recommended to have a dedicated root mountpoint for oscarapi which is not used by other applications. This to avoid creating a lot of unused baskets by the `ApiBasketMiddleWare`.

.. _mixed-usage-label:

Middleware and mixed usage
--------------------------

There are some middleware classes shipped with Oscar API which can be useful for your project. For example, we have seen in practice that it can be useful to mix plain Oscar and the API (fill your basket with the API and use plain Oscar views for checkout).

See the :doc:`/topics/middleware` section for more information.


