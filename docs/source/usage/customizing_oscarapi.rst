============================
Customizing Oscar API
============================

Oscarapi has a similar method of customization that you are used to from oscar.
That means you can override oscarapi's serializers and views in your own app,
with surgical precision.

Does it work the same way as oscar?
-----------------------------------

The only difference between how overriding works in oscar and in oscarapi is
that you have to make explicit where you will put your overriding classes.
The reason for this is that oscarapi is not divided in separate apps, which
would be rather useless, because there are no models anywhere in oscarapi so
none of the mechanisms of django apps are used. Instead, oscarapi is only one
app and you must keep it in ``INSTALLED_APPS`` at all times. So you don't
replace it with your own app like you do with oscar. You also so not have to
_fork_ the app, like you are doing in oscar.

Configuration
-------------

The only thing you have to do, is tell oscarapi where it should look for
overrides. You can do this using the ``OSCARAPI_OVERRIDE_MODULES`` setting::

    OSCARAPI_OVERRIDE_MODULES = ["myapp.api_extensions"]

If you must, you can also have oscarapi look in multiple places for overrides::

    OSCARAPI_OVERRIDE_MODULES = ["myapp.api_extensions", "my_reusableapp.api_extensions"]

It is *NOT NEEDED* to put the extension packages in ``INSTALLED_APPS``. You
can do it, but it is not required for the overrides to be found.

Example
-------

So what would that look like? As long as you keep the same package structure in
your overrides as oscarapi, your overrides will be found::

    ├── mysite
    │   ├── __init__.py
    │   ├── app.py
    │   ├── conf.py
    │   ├── mycustomapi
    │   │   ├── __init__.py
    │   │   └── serializers
    │   │       ├── __init__.py
    │   │       ├── checkout.py
    │   │       └── product.py

In this case the mysite app has a package called mycustomapi and in it are
overrides for the product and the checkout serializers. The ``OSCARAPI_OVERRIDE_MODULES``
setting would look like this::

    OSCARAPI_OVERRIDE_MODULES = ["mysite.mycustomapi"]

Let's see what happens in the checkout serializer file
``mysite.mycustomapi.serializers.checkout``:

.. literalinclude:: ../../../override-example/mycustomapi/serializers/checkout.py

So this override would add a field to the json of a country called
``is_benelux_country``, and the content would be ``true`` when the country is in the Benelux.

The complete example above is available in the `Github repository of Oscar API`_ if you want to check it out.

.. _`Github repository of Oscar API`: https://github.com/django-oscar/django-oscar-api/tree/master/override-example

Missing overrides
-----------------

Not *EVERY* single thing is made overridable in oscarapi. In general, all the
serializers and all the views are made overridable. If you need to know if
a certain class in a certain file is overridable, you can check the file.

If the object is loaded with ``get_api_class`` you can override it in your
oscarapi extension. If it is loaded with ``get_class`` or ``get_model`` it is
an object from oscar and you should override it by
`forking the app <https://django-oscar.readthedocs.io/en/latest/topics/class_loading_explained.html>`_.

If you find that something is not overridable by ``get_api_class`` and you
think it should be, feel free to send us a pull request with an explanation.
