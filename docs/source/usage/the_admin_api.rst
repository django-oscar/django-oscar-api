=============
The Admin API
=============
The endpoints that Oscar API default exposes are mostly suitable for checkout: customers who wants to buy a product from your webshop. From Oscar API version 1.6 and upwards, an *Admin API* is also available and exposed. Some usecases for the *Admin API* are:

* Creating your own admin frontend application and use Oscar as the backend (managing your catalogue, partners etc)
* Use Oscar with the *Admin API* as a SAAS solution: let other developers and companies integrate Oscar with their products
* *Push synchronization* of stockrecords / products / categories / partners  instead of import scripts etc.

To gain access to the *Admin API* you will beed to be a staff user (``IsAdminUser`` in `DRF`_). The ``APIAdminPermission`` (see also :ref:`permissions-label`) is used to grant access to the different models in the *Admin API* and what you can do with them. So if you only have the *view* and *edit permissions* for the ``Product`` model you are only allowed to view and edit products. To delete products you need the *delete* permission as well.

Default this permission is inherited from `DjangoModelPermissions`_ with the addition that it respects the *view* permissions as well. You can customize this as described in :doc:`/usage/customizing_oscarapi`.

.. _`DRF`: https://www.django-rest-framework.org/
.. _`DjangoModelPermissions`: https://www.django-rest-framework.org/api-guide/permissions/#djangomodelpermissions

The *Admin API* is also accessible in the browsable API when your logged in user has access to it:

.. image:: ../images/admin-api.png
   :alt: The Admin API


