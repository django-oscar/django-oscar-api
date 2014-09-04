==============
Oscar REST API
==============

This package provides a RESTful API for `django-oscar`_.

.. _`django-oscar`: https://github.com/tangentlabs/django-oscar
.. _`django-oscar@googlegroups.com`: https://groups.google.com/forum/?fromgroups#!forum/django-oscar
.. _`on the wiki`: https://github.com/tangentlabs/django-oscar-api/wiki

Rest api Gateway & resource protection.
---------------------------------------

Because we need the rest api to fascilitate the same usage patterns as
a regular oscar html frontend, we need protection of resources on several
levels.

1. gateway level.
   An api token is required to communicate with the rest api.
   That means we can authorize client applications to make use of the
   rest api. Examples of client applications are the sitecore website or a
   mobile application.
2. User level. Because we don't want resource protection to be the
   responsibility of the client application, we need restrictions of resource
   access on a user level. The user will use the rest api through an authorized
   client application. A user must only be able to access his own resources and
   it must be strictly enforced inside the rest api, that there is no way an
   api client application can access resources of a different user than the one
   identified to the rest api. Effectively an authorized client application can
   only manipulate resources on a user level and not on an administrator level.


Anonymous users
---------------

Just like the oscar html frontend, some part of the functionality of oscar is
available to anonymous users. That doesn't mean an anonymous user can not be
identified. They are identified by their session, the same way as in a regular
html frontend.

There is an upgrade path for an anonymous user, to become an authenticated user,
which opens up the functionality restricted to authenticated users, such as
checkout, order history etc.

A client application can upgrade a user by using the login api.
The following actions will be performed when a user logs in:

1. The user will be authenticated with gigya. The following steps will only be
   performed is login is succesful.
2. The anonymous cart will be merged with the private cart associated with that
   authenticated user.
3. A new session will be started, this session identifies the authenticated user
   for the duration of the session, without further calls to gigya.
4. The new, merged cart will be associated with this session.
5. The anonymous session will be terminated.
5. A response will be issued containing the new session id as a header (more on
   this later).

Session protocol
----------------

The rest api will not make use of cookies, which are usually used for
transferring the session id between the client and the backend. Instead we
will use the ``Session-Id`` header as specified in http://www.w3.org/TR/WD-session-id

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


An example of a session identifier would be: ``SID:ANON:www.nuticia.nl:82d7ac3f-135c-4b12-a296-ff3c4701307d``.
This identifier will be hashed to fit in 40 bytes to yield the final session key.

The ``thread`` and ``count`` values, while allowed will be ignored and not
included when hashing. When upgrading a user from anonymous to authenticated, a
new session id will be generated, by replacing ``ANON`` in the original session
id with ``AUTH`` and performing the hashing again, example: 

``SID:AUTH:www.nuticia.nl:82d7ac3f-135c-4b12-a296-ff3c4701307d``.

Every response of the REST will also contain the ``Session-Id`` header.
When a user is logged in, The response will contain a DIFFERENT Session-Id as
the request, because ANON will be replaced with AUTH.

Note that the generation of the ``identifier`` is a responsibility of the client
application, as specified in the w3c specification. This means that it remains
possible for a client application to resume sessions, as long as the identifier
is kept.

Client applications MUST ensure that session id's are unique, since it must
uniquely identify a user, in the same way as a user name.

Why?
----

The above measures ensure the following behaviour:

1. Anonymous sessions can be resumed indefinately, preventing loss of shopping
   basket content.
2. Differentiating Session Identification URI's between anonymous users and
   authenticated users prevents accidental retrieval of a private shopping basket
   for a user that has logged out of the client application.
3. Keeping the session identifier part of the Session Identification URI the same
   for both anonymous and authenticated users, simplifies tracking and associating
   rest api resources with client application resources.

Final note
----------

Note that guessing the ``identifier`` of an authenticated or anonymous user and
therefor hyjacking the session, is nomore difficult then guassing the session id
stored in a cookie for a web application.