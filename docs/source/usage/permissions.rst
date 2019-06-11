========================
Permissions and security
========================

Some notes on gateway & resource protection.
--------------------------------------------

Because we need the REST API to fascilitate the same usage patterns as
a regular oscar HTML frontend, we need protection of resources on several
levels.

1. `Gateway level`. An API token can be used to communicate with the REST API.
   That means we can authorize client applications to make use of the
   REST API. Examples of client applications are a website or a
   mobile application. See also the :ref:`gateway-middleware-label`.
2. `User level.` Because we don't want resource protection to be the
   responsibility of the client application, we need restrictions of resource
   access on a user level. The user will use the REST API through an authorized
   client application. A user must only be able to access his own resources and
   it must be strictly enforced inside the REST API, that there is no way an
   API client application can access resources of a different user than the one
   identified to the REST API. Effectively an authorized client application can
   only manipulate resources on a user level and not on an administrator level.
   See aso the :ref:`main-settings-label`.


Anonymous users
---------------

Just like the oscar HTML frontend, some part of the functionality of oscar is
available to anonymous users. That doesn't mean an anonymous user can not be
identified. They are identified by their session, the same way as in a regular
HTML frontend.

There is an upgrade path for an anonymous user, to become an authenticated user,
which opens up the functionality restricted to authenticated users.

A client application can upgrade a user by using the login API, See also
the :ref:`login-user-label` example.


The following actions will be performed when a user logs in:

1. The user will be authenticated with the REST API. The next steps will only be
   performed is login is succesful.
2. The anonymous cart will be merged with the private cart associated with that
   authenticated user.
3. A new session will be started, this session identifies the authenticated user
   for the duration of the session.
4. The new, merged cart will be associated with this session.
5. The anonymous session will be terminated.
6. A response will be issued containing the new session id.


.. _permissions-label:

Permissions
-----------

The Django REST Framework already supplies it's own defined permissions to make
sure that you can define which user can do what (PUT or just GET etc.). Oscar API
is using the following permissions, which you can use in your own views:

.. automodule:: oscarapi.permissions
   :members:
