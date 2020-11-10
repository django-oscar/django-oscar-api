==================
Oscar API Settings
==================

.. _main-settings-label:

Main settings
=============

``OSCARAPI_BLOCK_ADMIN_API_ACCESS``
-----------------------------------
Default: ``True``

Useful in production websites wehere you want to make sure that the admin api is not exposed at all.

``OSCARAPI_EXPOSE_USER_DETAILS``
-----------------------------------
Default: ``False``

The ``Login`` view (``GET``) and the ``owner`` field in the ``BasketSerializer`` and ``CheckoutSerializer`` expose user details, like username and email address. With this setting you can enable/disable this behaviour.

``OSCARAPI_ENABLE_REGISTRATION``
--------------------------------
Default: ``False``

Enables the ``register`` endpoint so it's possible to create new user accounts.

Serializer settings
===================

Most of the model serializers in Oscar API have a default set of fields to use in the REST API. If you customized the Oscar models you can reflect this customization by adding settings for this serializer.

For example, the ``RecommendedProduct`` serializer is defined as following:

.. code-block:: python

    class RecommmendedProductSerializer(OscarModelSerializer):
        url = serializers.HyperlinkedIdentityField(view_name='product-detail')

        class Meta:
            model = Product
            fields = overridable(
                'OSCARAPI_RECOMMENDED_PRODUCT_FIELDS',
                default=('url',)
            )

When you add the following section to your ``settings.py`` you will add the 'title' field as well:

.. code-block:: python

    OSCARAPI_RECOMMENDED_PRODUCT_FIELDS = ('url', 'title')


The following serializers have customizable field settings:

Basket serializers
------------------

.. autoclass:: oscarapi.serializers.basket.BasketSerializer
.. autoclass:: oscarapi.serializers.basket.BasketLineSerializer
.. autoclass:: oscarapi.serializers.basket.VoucherSerializer

Checkout serializers
--------------------

.. autoclass:: oscarapi.serializers.checkout.OrderSerializer
.. autoclass:: oscarapi.serializers.checkout.OrderLineSerializer
.. autoclass:: oscarapi.serializers.checkout.InlineSurchargeSerializer
.. autoclass:: oscarapi.serializers.checkout.UserAddressSerializer

Login serializers
-----------------

.. autoclass:: oscarapi.serializers.login.UserSerializer

Product serializers
-------------------

.. autoclass:: oscarapi.serializers.product.OptionSerializer
.. autoclass:: oscarapi.serializers.product.ProductLinkSerializer
.. autoclass:: oscarapi.serializers.product.RecommmendedProductSerializer
.. autoclass:: oscarapi.serializers.product.ChildProductSerializer
.. autoclass:: oscarapi.serializers.product.ProductSerializer
.. autoclass:: oscarapi.serializers.product.ProductAttributeSerializer
.. autoclass:: oscarapi.serializers.product.ProductAttributeValueSerializer

