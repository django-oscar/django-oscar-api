====================
Oscar API Middleware
====================
Oscar API ships with some useful middelware classes for session management, to restrict access to your API and make sure that you can mix an Oscar stand-alone website and the API.

Basket Middleware
=================
This is a replacement middleware for ``oscar.apps.basket.middleware.BasketMiddleware`` With this middleware, you can mix the API and
regular oscar views (also for anonymous users).

 .. autoclass:: oscarapi.middleware.ApiBasketMiddleWare

.. _header-session-label:

Header Session Middleware
=========================

This middleware is very useful when sessions are managed by an external website which commuicates with Oscar API.

.. class:: oscarapi.middleware.HeaderSessionMiddleware

The Header Session Middleware replaces the cookie based session middleware of Django when sessions are maintained by an external application / website based on the http://www.w3.org/TR/WD-session-id standard.

.. caution::
    The session protocol should only be used when a *TRUSTED* application needs to
    perform operations on behalf of a user. Never use the session protocol in any
    application where the requests can be inspected by an attacker, such as a
    mobile application. CSRF protection is NOT applied so requests CAN be forged
    when using the session protocol. Regular cookie based sessions are still
    fully functional and the entire REST API should work with this method of
    authentication as well. When using cookie based session, csrf restrictions
    are enforced as usual, so this is the preferred method of authentication
    for any untrusted applications.

.. important::
    When using the session protocol, the client application is 100% responsible
    for making sure session id's uniquely identify users. A session CAN and
    WILL be attached to another user if that user logs in with a session id
    allready in use by someone else.

When using the session protocol for authentication, the REST API will not make
use of cookies, which are usually used for transferring the session id between
the client and the backend. Instead we will use the ``Session-Id`` header as
specified in http://www.w3.org/TR/WD-session-id

The w3c Session Identification URI specification proposes a format for a session
identifier as follows::

    SID:type:realm:identifier[-thread][:count]
    Where the fields type, realm, identifier. thread and count are defined as follows:

    type
        Type of session identifier. This field allows other session identifier types to be defined. This draft specifies the identifier type "ANON".
    realm
        Specifies the realm within which linkage of the identifier is possible. Realms have the same format as DNS names.
    identifier
        Unstructured random integer specific to realm generated using a procedure with a negligible probability of collision. The identifier is encoded using base 64.
    thread
        Optional extension of identifier field used to differentiate concurrent uses of the same session identifier. The thread field is an integer encoded in hexadecimal.
    count
        Optional Hexadecimal encoded Integer containing a monotonically increasing counter value. A client should increment the count field after each operation.


An example of a session identifier would be: ``SID:ANON:www.example.com:82d7ac3f-135c-4b12-a296-ff3c4701307d``.
This identifier will be hashed to fit in 40 bytes to yield the final session key.

The ``thread`` and ``count`` values, while allowed will be ignored and not
included when hashing. When upgrading a user from anonymous to authenticated, a
new session id will be generated, by replacing ``ANON`` in the original session
id with ``AUTH`` and performing the hashing again, example:

``SID:AUTH:www.example.com:82d7ac3f-135c-4b12-a296-ff3c4701307d``.

Every response of the REST API will also contain the ``Session-Id`` header.
When a user is logged in, The response will contain a DIFFERENT Session-Id as
the request, because ANON will be replaced with AUTH.

Note that the generation of the ``identifier`` is a responsibility of the client
application, as specified in the w3c specification. This means that it remains
possible for a client application to resume sessions, as long as the identifier
is kept.

Client applications MUST ensure that session id's are unique, since it must
uniquely identify a user, in the same way as a user name.

.. important::

    The above measures ensure the following behaviour:

    1. Anonymous sessions can be resumed indefinately, preventing loss of shopping
       basket content.
    2. Differentiating Session Identification URI's between anonymous users and
       authenticated users prevents accidental retrieval of a private shopping basket
       for a user that has logged out of the client application.
    3. Keeping the session identifier part of the Session Identification URI the same
       for both anonymous and authenticated users, simplifies tracking and associating
       REST API resources with client application resources.

.. note::

    Note that guessing the ``identifier`` of an authenticated or anonymous user and
    therefor hijacking the session, is nomore difficult then guessing the session id
    stored in a cookie for a web application.

    Also note that the identifier, which is in the Session Identification URI, not
    used as the session id directly, which means session id's gathered from cookies
    can not be used to authenticate with the header Session-Id


.. _gateway-middleware-label:

Gateway MiddleWare
==================
Protects the usage of your API with an authentication token (we call it an ApiKey). To use this, add this as the first middleware in the MIDDLEWARE setting in your ``settings.py``.

.. autoclass:: oscarapi.middleware.ApiGatewayMiddleWare

To use this, you need to add an `ApiKey` object in the Django admin called ``MyKey``. From now on you need to send a HTTP ``Authorization: MyKey`` header when communicating with the API.


See also:
 .. autoclass:: oscarapi.models.ApiKey
