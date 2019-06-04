=============
The Admin API
=============
The endpoints that Oscar API defaultly exposes are mostly suitable for checkout: somebody who wants to buy a product from your webshop. From Oscar API version 1.6 and upwards, an *Admin API* is also available and exposed. This is suitable for a lot of things like:

* Creating your own admin frontend application and use Oscar as the backend (managing your catalogue, stock, partners etc)
* Use Oscar with the *Admin API* as a SAAS solution: let other developers and companies integrate Oscar with their products
* *Push synchronization* of stockrecords / products / categories / partners  instead of import scripts etc.

The ``APIAdminPermission`` (see also :ref:`permissions-label`) is used to grant access to the *Admin API*. Default this permission is  derived from `DjangoModelPermissions`_, but you can customize this as described in :doc:`/usage/customizing_oscarapi`.

.. _`DjangoModelPermissions`: https://www.django-rest-framework.org/api-guide/permissions/#djangomodelpermissions

The *Admin API* is also accessible in the browsable API:

.. image:: ../images/admin-api.png
   :alt: The Admin API


