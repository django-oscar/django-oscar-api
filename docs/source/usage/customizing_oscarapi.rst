============================
Customizing Oscar API
============================

By using the `django-rest-framework`_ life has become easy, at least for customizing the Oscar API. Oscar API exists of a collection of views and serializers which can be overriden by following the steps below.

.. note::
    In oscar you can `fork an app`_ to easily customize only the things you want to change.

.. _`fork an app`: http://django-oscar.readthedocs.org/en/releases-1.1/topics/fork_app.html
.. _`django-rest-framework`: http://www.django-rest-framework.org

Oscar API is using the basics of this so you can see Oscar API as one of the apps you customized just like in Oscar. Each Oscar app (or forked app) has a ``app.py`` which manages the url's to your custom views. 

In Oscar API the entry point of this is ``oscarapi.app:RESTApiApplication``.

In your own app, you can extend this class, and override some of the urls to
direct them to your own views. You can subclass any of the views in oscarapi,
or just write your own from scratch.

So, to modify some of the functionality in oscarapi, do the following:

1. In your project, create a new django app with ``manage.py startapp mycustomapi``.
2. In your app, create a file named ``app.py`` and in there extend ``oscarapi.app:RESTApiApplication``, like the following example:


.. code-block:: python

    from oscarapi.app import RESTApiApplication

        class MyRESTApiApplication(RESTApiApplication):

            def get_urls(self):
                urls = super(MyRESTApiApplication, self).get_urls()
                return urls

.. note::
    If you think that this is not changing anything (yet) then this is correct, see below.


3. Include your own app in INSTALLED_APPS instead of ``django-oscar-api`` (and add ``django-oscar-api`` to your app's dependencies) and see if this works.
4. Add a view which you want to change from Oscar API in your ``mycustomapi`` app  and add this to your app's ``urls.py``. In this example we override the ``get_queryset`` method of the ProductList view as we want to filter on locale (which we added to the Product model):

`views.py`

.. code-block:: python

    from django.utils.translation import get_language
    from oscarapi.views import basic


    class ProductList(basic.ProductList):
        def get_queryset(self):
            language = get_language()

            return super(ProductList, self).get_queryset().filter(
                locale=to_locale(language))

`urls.py`

.. code-block:: python

    from django.conf.urls import patterns, url
    from rest_framework.urlpatterns import format_suffix_patterns
    from myproject.mycustomapi import views

    urlpatterns = patterns(
        '',
        url(r'^products/$', views.ProductList.as_view(),
            name='product-list'),
   )

    urlpatterns = format_suffix_patterns(urlpatterns)


5. Adjust your ``mycustomapi.app:MyRESTApiApplication`` with your custom urls:

.. code-block:: python

    from oscarapi.app import RESTApiApplication

    from myproject.mycustomapi.urls import urlpatterns

        class MyRESTApiApplication(RESTApiApplication):

            def get_urls(self):
                urls = super(MyRESTApiApplication, self).get_urls()
                return urlpatterns + urls
