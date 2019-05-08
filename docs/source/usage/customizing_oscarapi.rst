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

    ├── demosite
    │   ├── __init__.py
    │   ├── app.py
    │   ├── conf.py
    │   ├── mycustomapi
    │   │   ├── __init__.py
    │   │   └── serializers
    │   │       ├── __init__.py
    │   │       ├── checkout.py
    │   │       └── product.py

In this case the demosite app has a package called mycustomapi and in it are
overrides for the product and the checkout serializers. The ``OSCARAPI_OVERRIDE_MODULES``
setting would look like this::

    OSCARAPI_OVERRIDE_MODULES = ["demosite.mycustomapi"]

Let's see what happens in the checkout serializer file
``demosite.mycustomapi.serializers.checkout``::

.. literalinclude:: ../../../demosite/mycustomapi/serializers/checkout.py

So this override would add a field to the json of a country called
``proof_of_functionality``, and the content would always be "HELLOW WORLD"

The complete example above is available in the `Github repository of Oscar API`_ if you want to try it out.

.. _`Github repository of Oscar API`: https://github.com/django-oscar/django-oscar-api/tree/master/demosite/
