=================
Oscar API Signals
=================

An overview of the signals defined by Oscar API.

``oscarapi_post_checkout``
--------------------------

.. class:: oscarapi.signals.oscarapi_post_checkout

    Raised when an order is successfully placed with the checkout API call

Arguments sent with this signal:

.. attribute:: order 

    The currently placed order

.. attribute:: user

    The user in question

.. attribute:: request

    The request instance

.. attribute:: response

    The response instance
