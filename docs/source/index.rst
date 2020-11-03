.. Django Oscar API documentation master file, created by
   sphinx-quickstart on Wed Dec 23 16:04:47 2015.

================
Django Oscar API
================
This package provides a RESTful API for `django-oscar`_, it's based on `django-rest-framework`_ and it exposes most of Oscar's functionality. You can find `the source code`_ on GitHub. If you have any questions or problems using Oscar API, please use the Github issuetracker.

.. _`django-oscar`: https://github.com/django-oscar/django-oscar
.. _`django-rest-framework`: http://www.django-rest-framework.org
.. _`the source code`: https://github.com/django-oscar/django-oscar-api


Requirements:
-------------
- Ppython 3.6 / 3.7 / 3.8
- Oscar >= 2.1
- Django 2.2 / 3.0
- Django Rest Framework >= 3.9

This version of Oscar API dropped support for Python 2 and Django 1.11 completely.

See `Travis`_ for the current tested platforms.

.. _`travis`: https://travis-ci.org/django-oscar/django-oscar-api


.. _django-oscar-api-installation:

Installation
------------
Please see the installation instructions of `Oscar`_ to install Oscar and how to create your own project. Then you can install Oscar API by simply typing:

.. _`Oscar`: https://django-oscar.readthedocs.io

.. code-block:: bash

    $ pip install django-oscar-api

Or you could add ``django-oscar-api`` to your project dependencies.

.. note::

    If you would like to install the current development version, use this:

    .. code-block:: bash

        $ pip install git+https://github.com/django-oscar/django-oscar-api.git


Use out-of-the-box
------------------

You can use the oscarapi application in an oscar ecommerce site without any customization. See for more information: :doc:`/usage/outofthebox`


.. _django-oscar-sandbox:

Play around with the sandbox
----------------------------
You can also install Oscar API from source and run the sandbox site to play around a bit. Make sure to create a virtualenv first.

.. code-block:: bash

    $ mkvirtualenv oscarapi
    $ git clone https://github.com/django-oscar/django-oscar-api.git
    $ cd django-oscar-api
    $ make sandbox

    # run the server
    $ python sandbox/manage.py runserver

Now you can browse the API at http://localhost:8000/api. Here you can actually use the API already (a cool feature of `django-rest-framework`_) by using your browser and test which JSON formats you can send/receive.


But I want to customise the standard serializers / views!
---------------------------------------------------------

Probably you want this, because you already extended or changed Oscar's functionality by forking it's apps right? See :doc:`/usage/customizing_oscarapi` for this.


.. toctree::
   :hidden:
   :maxdepth: 1

   usage/outofthebox
   usage/communicate_with_the_api
   usage/customizing_oscarapi
   usage/the_admin_api
   usage/middleware
   usage/settings
   usage/permissions
   usage/signals
   changelog.rst

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`

