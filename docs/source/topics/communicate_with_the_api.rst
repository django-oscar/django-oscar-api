========================
Communicate with the API
========================
When you browse through the API (see also the :ref:`django-oscar-sandbox` section), most of the things are already pretty clear in terms how you can communicate with the API. In the following examples we use the python `requests`_ package to demonstate how the API works.

.. _`requests`: http://docs.python-requests.org/

Start a session
----------------
In the following examples we use a session object to interact with the API. The session objects stores and
sends cookies automatically for us so the following gets you started for the examples shown here:

.. code-block:: python

    import requests

    # this will persist the session cookies automatically for us
    session = requests.Session()


Get the basket
--------------
First get our basket and see the response:

.. code-block:: python

    response = session.get('http://localhost:8000/api/basket/')
    print(response.content)
    {
        "currency": null,
        "id": 1,
        "is_tax_known": true,
        "lines": "http://localhost:8000/api/baskets/1/lines/",
        "offer_discounts": [],
        "owner": null,
        "status": "Open",
        "total_excl_tax": "0.00",
        "total_excl_tax_excl_discounts": "0.00",
        "total_incl_tax": "0.00",
        "total_incl_tax_excl_discounts": "0.00",
        "total_tax": "0.00",
        "url": "http://localhost:8000/api/baskets/1/",
        "voucher_discounts": []
    }

.. note::
    We need to re-send the cookies (wich include the `django session id`) to make sure we get the same basket again, this is the reason we use ``requests.Session()``. Otherwise we would get a new basket each request. So it's important to keep a track of sessions in your application. You can also use an alternative session middleware like the :ref:`header-session-label`.

.. code-block:: python

    response = session.get('http://localhost:8000/api/basket/')
    # we get the same basket when we send the session cookie
    print(response.json()['id'])
    1

To see what's inside the basket we need to get the basket lines:

.. code-block:: python

    lines_url = response.json()['lines']
    response = session.get(lines_url)
    # we don't have any lines yet because we did not put anything in the basket
    print(response.content)
    []


Add products to the basket
--------------------------
To add a product to the basket we first need to get the available products:

.. code-block:: python

    response = session.get('http://localhost:8000/api/products/')
    print(response.content)
    [
        {
            "id": 2,
            "title": "",
            "url": "http://localhost:8000/api/products/2/"
        },
        {
            "id": 1,
            "title": "Oscar T-shirt",
            "url": "http://localhost:8000/api/products/1/"
        }
    ]

You can fetch the detail of each product by following it's url:

.. code-block:: python

    products = response.json()
    # get the details of the second product
    response = session.get(products[1]['url'])
    print(response.content)
    {
        "attributes": [
            {
                "name": "Size",
                "value": "Small"
            }
        ],
        "availability": "http://localhost:8000/api/products/1/availability/",
        "categories": [
            "Clothing"
        ],
        "date_created": "2013-12-12T16:33:57.426000Z",
        "date_updated": "2013-12-12T16:33:57.426000Z",
        "description": "",
        "id": 1,
        "images": [],
        "options": [],
        "price": "http://localhost:8000/api/products/1/price/",
        "product_class": "T-shirt",
        "recommended_products": [],
        "stockrecords": "http://localhost:8000/api/products/1/stockrecords/",
        "title": "Oscar T-shirt",
        "url": "http://localhost:8000/api/products/1/"
    }

We want the blue version, so let's check the product options:

.. code-block:: python

    response = session.get('http://localhost:8000/api/options/')

    print(response.content)
    [
        {
            "url": "http://localhost:8000/api/options/1/",
            "id": 1,
            "name": "Color",
            "code": "color",
            "type": "Required"
        }
    ]

    option_url = self.response.json()[0]['url']

Ok, now we want to add this to our basket:

.. code-block:: python

    data = {
        "url": products[1]['url'],
        "quantity": 1,
        "options": [{
            "option": option_url, "value": "blue"
        }]
    }

    response = session.post('http://localhost:8000/api/basket/add-product/', json=data)

And we can see that it has been added:

.. code-block:: python

    response = session.get('http://localhost:8000/api/basket/')
    lines_url = response.json()['lines']
    response = session.get(lines_url)
    print(response.content)
    [
        {
            "attributes": [
                {
                    'option': 'http://localhost:8000/api/options/1/',
                    'url': 'http://localhost:8000/api/lineattributes/1/',
                    'value': 'blue'
                }
            ],
            "basket": "http://localhost:8000/api/baskets/1/",
            "date_created": "2015-12-30T17:05:05.041698Z",
            "is_tax_known": true,
            "price_currency": "EUR",
            "price_excl_tax": "10.00",
            "price_excl_tax_excl_discounts": "10.00",
            "price_incl_tax": "10.00",
            "price_incl_tax_excl_discounts": "10.00",
            "product": "http://localhost:8000/api/products/1/",
            "quantity": 1,
            "stockrecord": "http://localhost:8000/api/stockrecords/1/",
            "url": "http://localhost:8000/api/lines/1/",
            "warning": null
        }
    ]

Update or delete basket lines
-----------------------------

You can use a REST PUT and DELETE to update/delete the basket lines. So let's update the quantity for example:

.. code-block:: python

    # first get our line
    response = session.get('http://localhost:8000/api/basket/')
    response = session.get(response.json()['lines'])
    line_url = response.json()[0]['url']

    # now update the quantity
    data = {
        "quantity": 3
    }
    response = session.patch(line_url, data)

    # and we can see it's been updated
    print(response.content)
    {
        "attributes": [
            {
                'option': 'http://localhost:8000/api/options/1/',
                'url': 'http://localhost:8000/api/lineattributes/1/',
                'value': 'blue'
            }
        ],
        "basket": "http://localhost:8000/api/baskets/1/",
        "date_created": "2016-03-05T21:09:52.664388Z",
        "line_reference": "1_1",
        "price_currency": "EUR",
        "price_excl_tax": "10.00",
        "price_incl_tax": "10.00",
        "product": "http://localhost:8000/api/products/1/",
        "quantity": 3,
        "stockrecord": "http://localhost:8000/api/stockrecords/1/",
        "url": "http://localhost:8000/api/lines/1/"
    }

    # and our basket recalculated the total as well:
     response = session.get('http://localhost:8000/api/basket/')
     print(response.content.json()["total_incl_tax"])
     30.00

You can also update the color to red if you like:

.. code-block:: python

    line_attribute_url = response.content.json()['attributes'][0]['url']

    data = {
        "value": "red"
    }

    session.patch(line_attribute_url, data)


Now we will delete this line, it will return a 204 when it's successful:

.. code-block:: python

    response = session.delete(line_url)
    print(response.status_code)
    204

    # we can verify that the basket is empty now
    response = session.get('http://localhost:8000/api/basket/')
    lines_url = response.json()['lines']
    response = session.get(lines_url)
    print(response.content)
    []

Place an order (checkout)
-------------------------

When your basket is filled an you want to proceed to checkout you can do a
single call with all information needed. Note that we are doing an anonymous
checkout here, so we need to set the `guest_email` field. (Make sure that
``OSCAR_ALLOW_ANON_CHECKOUT`` is set to ``True`` in your ``settings.py``).
If you don't support anonymous checkouts you will have to login the user first
(see the :ref:`register-user-label` and :ref:`login-user-label` sections).

.. code-block:: python

    guest_email = "foo@example.com"

    # get our basket information
    response = session.get('http://localhost:8000/api/basket/')
    basket_data = response.json()

    # oscar needs a country for the shipping address. You can get a list of
    # the available countries with the api
    response = session.get('http://localhost:8000/api/countries/')
    countries = response.json()
    print(countries)
    [
        {
            "display_order": 0,
            "is_shipping_country": true,
            "iso_3166_1_a3": "NLD",
            "iso_3166_1_numeric": "528",
            "name": "Kingdom of the Netherlands",
            "printable_name": "Netherlands",
            "url": "http://127.0.0.1:8000/api/countries/NL/"
        }
    ]

    # we need the country url in the shipping address
    country_url = countries[0]['url']

    # we need to check the available shipping options
    response = session.get('http://localhost:8000/api/basket/shipping-methods/')
    shipping_methods = response.json()
    print(shipping_methods)
    [
        {
            "code": "free-shipping",
            "name": "Free shipping",
            "price": {
                "currency": "EUR",
                "excl_tax": "0.00",
                "incl_tax": "0.00",
                "tax": "0.00"
            }
        }
    ]

    # pick one
    shipping_method = shipping_methods[0]

    # let's fill out the request data
    data = {
        "basket": basket_data['url'],
        "guest_email": guest_email,
        "total": basket_data['total_incl_tax'],
        "shipping_method_code": shipping_method['code'],
        # the shipping charge is optional, but we leave it here for example purposes
        "shipping_charge": {
            "currency": basket_data['currency'],
            "excl_tax": "0.0",
            "tax": "0.0"
        },
        "shipping_address": {
            "country": country_url,
            "first_name": "Henk",
            "last_name": "Van den Heuvel",
            "line1": "Roemerlaan 44",
            "line2": "",
            "line3": "",
            "line4": "Kroekingen",
            "notes": "",
            "phone_number": "+31 26 370 4887",
            "postcode": "7777KK",
            "state": "Gerendrecht",
            "title": "Mr"
        }
    }

    # you can specify a different billing address if you want to
    data['billing_address'] = {
        "country": country_url,
        "first_name": "Jos",
        "last_name": "Henken",
        "line1": "Boerderijstraat 19",
        "line2": "",
        "line3": "",
        "line4": "Zwammerdam",
        "notes": "",
        "phone_number": "+31 27 112 9800",
        "postcode": "6666LL",
        "state": "Gerendrecht",
        "title": "Mr"
     }

    # now we can place the order
    response = session.post('http://localhost:8000/api/checkout/', json=data)

    # and the api should give us a response with all info needed
    print (response.content)
    {
        "basket": "http://localhost:8000/api/baskets/1/",
        "billing_address": null,
        "currency": "EUR",
        "date_placed": "2016-01-02T23:18:01.089796Z",
        "guest_email": "foo@example.com",
        "lines": "http://localhost:8000/api/orders/1/lines/",
        # this is the order number generated in oscar
        "number": "10001",
        "offer_discounts": [],
        "owner": null,
        # the payment view is something you will have to implement yourself,
        # see the note below
        "payment_url": "You need to implement a view named 'api-payment' which redirects to the payment provider and sets up the callbacks.",
        "shipping_address": {
            "country": "http://localhost:8000/api/countries/NL/",
            "first_name": "Henk",
            "id": 3,
            "last_name": "Van den Heuvel",
            "line1": "Roemerlaan 44",
            "line2": "",
            "line3": "",
            "line4": "Kroekingen",
            "notes": "",
            "phone_number": "+31 26 370 4887",
            "postcode": "7777KK",
            "search_text": "Henk Van den Heuvel Roemerlaan 44 Kroekingen Gerendrecht 7777KK Kingdom of the Netherlands",
            "state": "Gerendrecht",
            "title": "Mr"
        },
        "shipping_code": "free-shipping",
        "shipping_excl_tax": "0.00",
        "shipping_incl_tax": "0.00",
        "shipping_method": "Free shipping",
        "status": "new",
        "total_excl_tax": "10.00",
        "total_incl_tax": "10.00",
        # you can fetch the order details by getting this url
        "url": "http://localhost:8000/api/orders/1/",
        "voucher_discounts": []
    }

.. note::
    After you placed an order with the api, the basket is frozen. Oscar API has checks for this in the checkout view and won't let you checkout the same (or any frozen) basket again. At this stage an order is submitted in Oscar and you will have to implement the following steps regarding payment yourself. See the ``payment_url`` field above in the response. You can also use the regular Oscar checkout views if you like, take a look at the :ref:`mixed-usage-label` section.

.. note::
    If your shipping methods depend in any way on the shipping address, you can
    also POST to the shipping_method api. Just post the shipping details in
    the same format as accepted by the checkout api::

      {
          "country": "http://localhost:8000/api/countries/NL/",
          "first_name": "Henk",
          "id": 3,
          "last_name": "Van den Heuvel",
          "line1": "Roemerlaan 44",
          "line2": "",
          "line3": "",
          "line4": "Kroekingen",
          "notes": "",
          "phone_number": "+31 26 370 4887",
          "postcode": "7777KK",
          "search_text": "Henk Van den Heuvel Roemerlaan 44 Kroekingen Gerendrecht 7777KK Kingdom of the Netherlands",
          "state": "Gerendrecht",
          "title": "Mr"
      }

.. note::
    In the checkout view of Oscar, the function ``handle_successful_order`` is called after placing an order. This sends the order confirmation message, flushes your session and sends the ``post_checkout`` signal. The Oscar API checkout view is not calling this method by design. If you would like to send a confirmation message (or other stuff you need to do) after placing an order you can subscribe to the ``oscarapi_post_checkout`` signal, see :doc:`/topics/signals`.

.. note::
    An extension on top of django-oscar-api providing a more flexible checkout API with a pluggable payment methods
    is written by Craig Weber, see `django oscar api checkout`_

.. _`django oscar api checkout`: https://gitlab.com/thelabnyc/django-oscar/django-oscar-api-checkout

.. _login-user-label:

Login the user
--------------
When you don't support anonymous checkouts you will need to login first. Oscar API comes with a simple login view for this:

.. code-block:: python

    data = {
        "username": "test",
        "password": "test"
    }
    response = session.post('http://localhost:8000/api/login/', json=data)

.. note::
    Custom User models with a different username field are supported. In Oscar API this field will be mapped to the
    corresponding username field.

When the authentication was succesful, your will receive a new (authenticated) sessionid, and the anonymous basket has been automatically merged with a (previous stored) basket of this specific user. You can see now that the owner is set in the basket:

.. code-block:: python

    response = session.get('http://localhost:8000/api/basket/')
    print(response.content)
    {
        "currency": "EUR",
        "id": 2,
        "is_tax_known": true,
        "lines": "http://localhost:8000/api/baskets/2/lines/",
        "offer_discounts": [],
        # now, this basket has an owner
        "owner": "http://localhost:8000/api/users/2/",
        "status": "Open",
        "total_excl_tax": "10.00",
        "total_excl_tax_excl_discounts": "10.00",
        "total_incl_tax": "10.00",
        "total_incl_tax_excl_discounts": "10.00",
        "total_tax": "0.00",
        "url": "http://localhost:8000/api/baskets/2/",
        "voucher_discounts": []
    }

.. _register-user-label:

Register a new user
-------------------
Oscar API ships with a registration endpoint to create new accounts. The endpoint can be enabled using the ``OSCARAPI_ENABLE_REGISTRATION`` setting.

.. code-block:: python

    data = {
        "email": "my@emailaddress.com",
        "password1": "V3rYS3cr3t",
        "password2": "V3rYS3cr3t"
    }
    response = session.post('http://localhost:8000/api/register/', json=data)

When the creation of the user was succesful it will return a 201 HTTP Response. Aftter this you cam login the user
with the login endpoint, see :ref:`login-user-label`.
