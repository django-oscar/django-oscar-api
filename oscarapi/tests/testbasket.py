import json
import re

from django.conf import settings
from django.core.urlresolvers import reverse

from oscar.core.loading import get_model

from oscarapi.tests.utils import APITest


Basket = get_model('basket', 'Basket')


class BasketTest(APITest):
    fixtures = [
        'product', 'productcategory', 'productattribute', 'productclass',
        'productattributevalue', 'category', 'attributeoptiongroup', 'attributeoption',
        'stockrecord', 'partner'
    ]

    def setUp(self):
        # make sure we have this disabled for most of the tests
        settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = None
        super(BasketTest, self).setUp()

    def test_basket_api_create(self):
        "The basket api create command should work with regular cookie based login"
        url = reverse('basket-list')
        empty = Basket.objects.all()
        self.assertFalse(empty.exists(), "There should be no baskets yet.")

        # anonymous
        data = {}

        self.response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.response.assertStatusEqual(403, "Anonymous users can not use the basket api to create baskets.")

        # authenticated
        self.login('nobody', 'nobody')
        data = {'owner': "http://testserver%s" % reverse('user-detail', args=[2])}

        self.response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.response.assertStatusEqual(403, "Authenticated regular users can not use the basket api to create baskets.")

        # admin
        self.login('admin', 'admin')

        data = {'owner': "http://testserver%s" % reverse('user-detail', args=[1])}
        self.response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.response.assertStatusEqual(201, "It should be possible for a basket to be created, for a specific user.")
        self.response.assertObjectIdEqual('owner', 1)

        # When we created a basket, it should be listed in the basket-list view
        self.response = self.client.get(url, content_type='application/json')
        self.assertEqual(len(self.response.data), 1)

        data = {}
        self.response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.response.assertStatusEqual(201, "It should be possible for a basket to be created for an anonymous user.")
        self.assertEqual(Basket.objects.count(), 2, "2 baskets should after creating 2 baskets.")

    def test_basket_api_create_header(self):
        "The basket api create command should work with header based login."
        empty = Basket.objects.all()
        self.assertFalse(empty.exists(), "There should be no baskets yet.")

        if self.hlogin('nobody', 'nobody', session_id='nobody'):
            self.response = self.post('basket-list', session_id='nobody', authenticated=True,
                owner="http://testserver%s" % reverse('user-detail', args=[2])
            )
            self.response.assertStatusEqual(403, "Authenticated regular users can not use the basket api to create baskets.")

        if self.hlogin('admin', 'admin', session_id='admin'):
            self.response = self.post('basket-list', session_id='admin', authenticated=True,
                owner="http://testserver%s" % reverse('user-detail', args=[1])
            )
            self.response.assertStatusEqual(201, "It should be possible for a basket to be created, for a specific user.")
            self.response.assertObjectIdEqual('owner', 1)

        self.assertEqual(Basket.objects.count(), 3, "There should be 2 baskets from loging in and 1 is created with the api.")
            
    def test_retrieve_basket(self):
        "A user can fetch their own basket with the basket API and get's the same basket every time."
        # anonymous
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('owner', None)
        basket_id = self.response['id']

        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)
        
        # authenticated
        self.login('nobody', 'nobody')
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertObjectIdEqual('owner', 2)
        basket_id = self.response['id']

        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)

        # admin
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            self.login('admin', 'admin')
            self.response = self.get('api-basket')
            self.response.assertStatusEqual(200)
            self.response.assertObjectIdEqual('owner', 1)
            basket_id = self.response['id']

            self.response = self.get('api-basket')
            self.response.assertStatusEqual(200)
            self.response.assertValueEqual('id', basket_id)

        self.assertEqual(Basket.objects.count(), 3, "There should be 3 baskets open after 3 users accessed a basket.")

    def test_retrieve_basket_header(self):
        "Using header authentication the basket api should also work perfectly."
        # anonymous
        self.response = self.get('api-basket', session_id='anonymous')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('owner', None)
        basket_id = self.response['id']

        self.response = self.get('api-basket', session_id='anonymous')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)
        
        # authenticated
        self.hlogin('nobody', 'nobody', session_id='nobody')
        self.response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(200)
        self.response.assertObjectIdEqual('owner', 2)
        basket_id = self.response['id']

        self.response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)

        # admin
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            self.hlogin('admin', 'admin', session_id='admin')
            self.response = self.get('api-basket', session_id='admin', authenticated=True)
            self.response.assertStatusEqual(200)
            self.response.assertObjectIdEqual('owner', 1)
            basket_id = self.response['id']

            self.response = self.get('api-basket', session_id='admin', authenticated=True)
            self.response.assertStatusEqual(200)
            self.response.assertValueEqual('id', basket_id)

        self.assertEqual(Basket.objects.count(), 3, "There should be 3 baskets open after 3 users accessed a basket.")

    def test_basket_read_permissions(self):
        "A regular or anonymous user should not be able to fetch someone elses basket."
        # anonymous user can retrive a basket.
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response['url']
        basket_lines = self.response['lines']

        self.response = self.client.get(basket_url)
        self.response.assertStatusEqual(200)

        self.response = self.client.get(basket_lines)
        self.response.assertStatusEqual(200)

        # create a basket for somebody else
        b = Basket.objects.create(owner_id=2)
        self.assertEqual(str(b.owner), 'nobody')
        self.assertEqual(b.pk, 2)

        # try to acces somebody else's basket (hihi).
        url = reverse('basket-detail', args=(2,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users carts.")
        url = reverse('basket-lines-list', args=(2,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users cart items.")

        # now try for authenticated user.
        self.login('nobody', 'nobody')
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response['url']
        basket_lines = self.response['lines']

        self.response = self.client.get(basket_url)
        self.response.assertStatusEqual(200)

        self.response = self.client.get(basket_lines)
        self.response.assertStatusEqual(200)

        # try to acces somebody else's basket (hihi).
        url = reverse('basket-detail', args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users carts.")

        url = reverse('basket-lines-list', args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users cart items.")

        # now let's show the power of the admin!
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            self.login('admin', 'admin')
            self.response = self.get('api-basket')
            self.response.assertStatusEqual(200)

            # try to access the urls in the response.
            basket_url = self.response['url']
            basket_lines = self.response['lines']

            self.response = self.client.get(basket_url)
            self.response.assertStatusEqual(200)

            self.response = self.client.get(basket_lines)
            self.response.assertStatusEqual(200)

            # try to acces somebody else's basket (hihi).
            url = reverse('basket-detail', args=(1,))
            self.response = self.client.get(url)
            self.response.assertStatusEqual(200, "Staff users can access anything.")

            url = reverse('basket-lines-list', args=(1,))
            self.response = self.client.get(url)
            self.response.assertStatusEqual(200, "Staff users can access anything.")

        self.assertEqual(Basket.objects.count(), 3, "There should be 3 baskets open after 3 users accessed a basket.")

    def test_basket_read_permissions_header(self):
        "A regular or anonymous user should not be able to fetch someone elses basket, even when authenticating with a session header."
        # anonymous user can retrieve a basket.
        self.response = self.get('api-basket', session_id='anonymous')
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response['url']
        basket_lines = self.response['lines']

        self.response = self.client.get(basket_url, HTTP_SESSION_ID='SID:ANON:testserver:anonymous')
        self.response.assertStatusEqual(200)

        self.response = self.client.get(basket_lines, HTTP_SESSION_ID='SID:ANON:testserver:anonymous')
        self.response.assertStatusEqual(200)

        # create a basket for somebody else
        b = Basket.objects.create(owner_id=2)
        self.assertEqual(str(b.owner), 'nobody')
        self.assertEqual(b.pk, 2)

        # try to acces somebody else's basket (hihi).
        url = reverse('basket-detail', args=(2,))
        self.response = self.client.get(url, HTTP_SESSION_ID='SID:ANON:testserver:anonymous')
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users carts.")

        url = reverse('basket-lines-list', args=(2,))
        self.response = self.client.get(url, HTTP_SESSION_ID='SID:ANON:testserver:anonymous')
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users cart items.")

        # now try for authenticated user.
        self.hlogin('nobody', 'nobody', session_id='nobody')
        self.response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response['url']
        basket_lines = self.response['lines']

        self.response = self.client.get(basket_url, HTTP_SESSION_ID='SID:AUTH:testserver:nobody')
        self.response.assertStatusEqual(200)

        self.response = self.client.get(basket_lines, HTTP_SESSION_ID='SID:AUTH:testserver:nobody')
        self.response.assertStatusEqual(200)

        # try to acces somebody else's basket (hihi).
        url = reverse('basket-detail', args=(1,))
        self.response = self.client.get(url, HTTP_SESSION_ID='SID:AUTH:testserver:nobody')
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users carts.")

        url = reverse('basket-lines-list', args=(1,))
        self.response = self.client.get(url, HTTP_SESSION_ID='SID:AUTH:testserver:nobody')
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users cart items.")

        # now let's show the power of the admin!
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            self.hlogin('admin', 'admin', session_id='admin')
            self.response = self.get('api-basket', session_id='admin', authenticated=True)
            self.response.assertStatusEqual(200)

            # try to access the urls in the response.
            basket_url = self.response['url']
            basket_lines = self.response['lines']

            self.response = self.client.get(basket_url, HTTP_SESSION_ID='SID:AUTH:testserver:admin')
            self.response.assertStatusEqual(200)

            self.response = self.client.get(basket_lines, HTTP_SESSION_ID='SID:AUTH:testserver:admin')
            self.response.assertStatusEqual(200)

            # try to acces somebody else's basket (hihi).
            url = reverse('basket-detail', args=(1,))
            self.response = self.client.get(url, HTTP_SESSION_ID='SID:AUTH:testserver:admin')
            self.response.assertStatusEqual(200, "Staff users can access anything.")

            url = reverse('basket-lines-list', args=(1,))
            self.response = self.client.get(url, HTTP_SESSION_ID='SID:AUTH:testserver:admin')
            self.response.assertStatusEqual(200, "Staff users can access anything.")

        self.assertEqual(Basket.objects.count(), 3, "There should be 3 baskets open after 3 users accessed a basket.")

    def test_basket_write_permissions_anonymous(self):
        "An anonymous user should not be able to change someone elses basket."

        # anonymous user
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('status', 'Open')

        # try to access the urls in the response.
        basket_id = self.response['id']
        basket_url = self.response['url']

        # change status to saved
        url = reverse('basket-detail', args=(basket_id,))
        self.response = self.put(url, status='Saved')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)
        self.response.assertValueEqual('status', 'Saved')

        # and back to open again
        self.response = self.put(url, status='Open')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)
        self.response.assertValueEqual('status', 'Open')

        # write a line to the basket
        line_data = {
            "basket": basket_url, 
            "line_reference": "234_345", 
            "product": "http://testserver/api/products/1/", 
            "stockrecord": "http://testserver/api/stockrecords/1/", 
            "quantity": 3, 
            "price_currency": "EUR", 
            "price_excl_tax": "100.0", 
            "price_incl_tax": "121.0",
        }
        line_url = reverse('basket-lines-list', args=(basket_id,))
        self.response = self.post(line_url, **line_data)
        self.response.assertStatusEqual(201)

        # throw the basket away
        self.response = self.delete(url)
        self.response.assertStatusEqual(204)

        # now lets start messing around
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        basket_id = self.response['id']

        # create a basket for another user.
        b = Basket.objects.create(owner_id=2)
        self.assertEqual(str(b.owner), 'nobody')
        self.assertEqual(Basket.objects.count(), 2)
        nobody_basket_id = b.pk
        
        # try to access the urls in the response.
        basket_id = self.response['id']
        basket_url = self.response['url']
        url = reverse('basket-detail', args=(basket_id,))

        self.response.assertValueEqual('status', 'Open')

        # try to write to someone else's basket by sending the primary key
        # along.
        self.response = self.put(url, status='Saved', id=nobody_basket_id)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id, 'Primary key value can not be changed.')
        self.response.assertValueEqual('status', 'Saved')

        # try to write to someone else's basket directly
        url = reverse('basket-detail', args=(nobody_basket_id,))
        self.response = self.put(url, status='Saved')
        self.response.assertStatusEqual(403)

        # try to delete someone else's basket
        self.response = self.delete(url)
        self.response.assertStatusEqual(403)
        
        # try adding lines to someone elses basket
        line_data = {
            "basket": "http://testserver/api/baskets/%s/" % nobody_basket_id, 
            "line_reference": "234_345", 
            "product": "http://testserver/api/products/1/", 
            "stockrecord": "http://testserver/api/stockrecords/1/", 
            "quantity": 3, 
            "price_currency": "EUR", 
            "price_excl_tax": "100.0", 
            "price_incl_tax": "121.0"
        }
        url = reverse('basket-lines-list', args=(basket_id,))
        self.response = self.post(url, **line_data)
        self.response.assertStatusEqual(403)

    def test_basket_write_permissions_authenticated(self):
        "An authenticated user should not be able to change someone elses basket"

        # now try for authenticated user.
        self.login('nobody', 'nobody')
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_id = self.response['id']
        basket_url = self.response['url']
        owner_url = self.response['owner']
        self.assertIn(reverse('user-detail', args=(2,)), owner_url)
        self.response.assertValueEqual('status', 'Open')

        # change status to saved
        url = reverse('basket-detail', args=(basket_id,))
        self.response = self.put(url, status='Saved')

        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)
        self.response.assertValueEqual('status', 'Saved')

        # and back to open again
        self.response = self.put(url, status='Open')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)
        self.response.assertValueEqual('status', 'Open')

        # write a line to the basket
        line_data = {
            "basket": basket_url, 
            "line_reference": "234_345", 
            "product": "http://testserver/api/products/1/", 
            "stockrecord": "http://testserver/api/stockrecords/1/", 
            "quantity": 3, 
            "price_currency": "EUR", 
            "price_excl_tax": "100.0", 
            "price_incl_tax": "121.0",
        }
        line_url = reverse('basket-lines-list', args=(basket_id,))
        self.response = self.post(line_url, **line_data)
        self.response.assertStatusEqual(201)

        # throw the basket away
        self.response = self.delete(url)
        self.response.assertStatusEqual(204)

        # now lets start messing around
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        basket_id = self.response['id']

        # create a basket for another user.
        b = Basket.objects.create(owner_id=3)
        self.assertEqual(str(b.owner), 'somebody')
        self.assertEqual(Basket.objects.count(), 2)
        somebody_basket_id = b.pk

        # try to access the urls in the response.
        basket_id = self.response['id']
        basket_url = self.response['url']
        url = reverse('basket-detail', args=(basket_id,))

        self.response.assertValueEqual('status', 'Open')

        # try to write to someone else's basket by sending the primary key
        # along.
        self.response = self.put(url, status='Saved', id=somebody_basket_id)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id, 'Primary key value can not be changed.')
        self.response.assertValueEqual('status', 'Saved')

        # try to write to someone else's basket directly
        url = reverse('basket-detail', args=(somebody_basket_id,))
        self.response = self.put(url, status='Saved')
        self.response.assertStatusEqual(403)

        # try to delete someone else's basket
        self.response = self.delete(url)
        self.response.assertStatusEqual(403)

        # try adding lines to someone elses basket
        line_data = {
            "basket": "http://testserver/api/baskets/%s/" % somebody_basket_id,
            "line_reference": "234_345",
            "product": "http://testserver/api/products/1/",
            "stockrecord": "http://testserver/api/stockrecords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0"
        }
        url = reverse('basket-lines-list', args=(basket_id,))
        self.response = self.post(url, **line_data)
        self.response.assertStatusEqual(403)

    def test_basket_write_permissions_header_authenticated(self):
        "An authenticated user should not be able to change someone elses basket, when authinticating with session header."

        # now try for authenticated user.
        self.hlogin('nobody', 'nobody', session_id='nobody')
        self.response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_id = self.response['id']
        basket_url = self.response['url']
        owner_url = self.response['owner']
        self.assertIn(reverse('user-detail', args=(2,)), owner_url)
        self.response.assertValueEqual('status', 'Open')

        # change status to saved
        url = reverse('basket-detail', args=(basket_id,))
        self.response = self.put(url, status='Saved', session_id='nobody', authenticated=True)

        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)
        self.response.assertValueEqual('status', 'Saved')

        # and back to open again
        self.response = self.put(url, status='Open', session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)
        self.response.assertValueEqual('status', 'Open')

        # write a line to the basket
        line_data = {
            "basket": basket_url, 
            "line_reference": "234_345", 
            "product": "http://testserver/api/products/1/", 
            "stockrecord": "http://testserver/api/stockrecords/1/", 
            "quantity": 3, 
            "price_currency": "EUR", 
            "price_excl_tax": "100.0", 
            "price_incl_tax": "121.0",
        }
        line_url = reverse('basket-lines-list', args=(basket_id,))
        self.response = self.post(line_url, session_id='nobody', authenticated=True, **line_data)
        self.response.assertStatusEqual(201)

        # throw the basket away
        self.response = self.delete(url, session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(204)

        # now lets start messing around
        self.response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(200)
        basket_id = self.response['id']

        # create a basket for another user.
        b = Basket.objects.create(owner_id=3)
        self.assertEqual(str(b.owner), 'somebody')
        self.assertEqual(Basket.objects.count(), 2)
        somebody_basket_id = b.pk

        # try to access the urls in the response.
        basket_id = self.response['id']
        basket_url = self.response['url']
        url = reverse('basket-detail', args=(basket_id,))

        self.response.assertValueEqual('status', 'Open')

        # try to write to someone else's basket by sending the primary key
        # along.
        self.response = self.put(url, status='Saved', session_id='nobody', authenticated=True, id=somebody_basket_id)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id, 'Primary key value can not be changed.')
        self.response.assertValueEqual('status', 'Saved')

        # try to write to someone else's basket directly
        url = reverse('basket-detail', args=(somebody_basket_id,))
        self.response = self.put(url, status='Saved', session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(403)

        # try to delete someone else's basket
        self.response = self.delete(url, session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(403)

        # try adding lines to someone elses basket
        line_data = {
            "basket": "http://testserver/api/baskets/%s/" % somebody_basket_id,
            "line_reference": "234_345",
            "product": "http://testserver/api/products/1/",
            "stockrecord": "http://testserver/api/stockrecords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0"
        }
        url = reverse('basket-lines-list', args=(basket_id,))
        self.response = self.post(url, session_id='nobody', authenticated=True, **line_data)
        self.response.assertStatusEqual(403)

    def test_basket_write_permissions_admin(self):
        "An admin user can change someone elses basket."

        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            # now try for authenticated user.
            self.login('admin', 'admin')
            self.response = self.get('api-basket')
            self.response.assertStatusEqual(200)

            # try to access the urls in the response.
            basket_id = self.response['id']
            basket_url = self.response['url']
            owner_url = self.response['owner']
            self.assertIn(reverse('user-detail', args=(1,)), owner_url)
            self.response.assertValueEqual('status', 'Open')

            # change status to saved
            url = reverse('basket-detail', args=(basket_id,))
            self.response = self.put(url, status='Saved')

            self.response.assertStatusEqual(200)
            self.response.assertValueEqual('id', basket_id)
            self.response.assertValueEqual('status', 'Saved')

            # and back to open again
            self.response = self.put(url, status='Open')
            self.response.assertStatusEqual(200)
            self.response.assertValueEqual('id', basket_id)
            self.response.assertValueEqual('status', 'Open')

            # write a line to the basket
            line_data = {
                "basket": basket_url,
                "line_reference": "234_345",
                "product": "http://testserver/api/products/1/",
                "stockrecord": "http://testserver/api/stockrecords/1/",
                "quantity": 3,
                "price_currency": "EUR",
                "price_excl_tax": "100.0",
                "price_incl_tax": "121.0",
            }
            line_url = reverse('basket-lines-list', args=(basket_id,))
            self.response = self.post(line_url, **line_data)
            self.response.assertStatusEqual(201)

            # throw the basket away
            self.response = self.delete(url)
            self.response.assertStatusEqual(204)

            # now lets start messing around
            self.response = self.get('api-basket')
            self.response.assertStatusEqual(200)
            basket_id = self.response['id']

            # create a basket for another user.
            b = Basket.objects.create(owner_id=3)
            self.assertEqual(str(b.owner), 'somebody')
            self.assertEqual(Basket.objects.count(), 2)
            somebody_basket_id = b.pk

            # try to access the urls in the response.
            basket_id = self.response['id']
            basket_url = self.response['url']
            url = reverse('basket-detail', args=(basket_id,))

            self.response.assertValueEqual('status', 'Open')

            # try to write to someone else's basket by sending the primary key
            # along.
            self.response = self.put(url, status='Saved', id=somebody_basket_id)
            self.response.assertStatusEqual(200)
            self.response.assertValueEqual('id', basket_id, 'Primary key value can not be changed.')
            self.response.assertValueEqual('status', 'Saved')

            # try to write to someone else's basket directly
            url = reverse('basket-detail', args=(somebody_basket_id,))
            self.response = self.put(url, status='Saved')
            self.response.assertStatusEqual(200)

            # try adding lines to someone elses basket
            line_data = {
                "basket": "http://testserver/api/baskets/%s/" % somebody_basket_id,
                "line_reference": "234_345",
                "product": "http://testserver/api/products/1/",
                "stockrecord": "http://testserver/api/stockrecords/1/",
                "quantity": 3,
                "price_currency": "EUR",
                "price_excl_tax": "100.0",
                "price_incl_tax": "121.0"
            }
            zurl = reverse('basket-lines-list', args=(basket_id,))
            self.response = self.post(zurl, **line_data)
            self.response.assertStatusEqual(406)

            # try to delete someone else's basket
            self.response = self.delete(url)
            self.response.assertStatusEqual(204)

    def test_basket_write_permissions_header_admin(self):
        "An admin user can change someone elses basket, when authinticating with session header."
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            # now try for authenticated user.
            self.hlogin('admin', 'admin', session_id='admin')
            self.response = self.get('api-basket', session_id='admin', authenticated=True)
            self.response.assertStatusEqual(200)

            # try to access the urls in the response.
            basket_id = self.response['id']
            basket_url = self.response['url']
            owner_url = self.response['owner']
            self.assertIn(reverse('user-detail', args=(1,)), owner_url)
            self.response.assertValueEqual('status', 'Open')

            # change status to saved
            url = reverse('basket-detail', args=(basket_id,))
            self.response = self.put(url, status='Saved', session_id='admin', authenticated=True)

            self.response.assertStatusEqual(200)
            self.response.assertValueEqual('id', basket_id)
            self.response.assertValueEqual('status', 'Saved')

            # and back to open again
            self.response = self.put(url, status='Open', session_id='admin', authenticated=True)
            self.response.assertStatusEqual(200)
            self.response.assertValueEqual('id', basket_id)
            self.response.assertValueEqual('status', 'Open')

            # write a line to the basket
            line_data = {
                "basket": basket_url,
                "line_reference": "234_345",
                "product": "http://testserver/api/products/1/",
                "stockrecord": "http://testserver/api/stockrecords/1/",
                "quantity": 3,
                "price_currency": "EUR",
                "price_excl_tax": "100.0",
                "price_incl_tax": "121.0",
            }
            line_url = reverse('basket-lines-list', args=(basket_id,))
            self.response = self.post(line_url, session_id='admin', authenticated=True, **line_data)
            self.response.assertStatusEqual(201)

            # throw the basket away
            self.response = self.delete(url, session_id='admin', authenticated=True)
            self.response.assertStatusEqual(204)

            # now lets start messing around
            self.response = self.get('api-basket', session_id='admin', authenticated=True)
            self.response.assertStatusEqual(200)
            basket_id = self.response['id']

            # create a basket for another user.
            b = Basket.objects.create(owner_id=3)
            self.assertEqual(str(b.owner), 'somebody')
            self.assertEqual(Basket.objects.count(), 2)
            somebody_basket_id = b.pk

            # try to access the urls in the response.
            basket_id = self.response['id']
            basket_url = self.response['url']
            url = reverse('basket-detail', args=(basket_id,))

            self.response.assertValueEqual('status', 'Open')

            # try to write to someone else's basket by sending the primary key
            # along.
            self.response = self.put(url, status='Saved', session_id='admin', authenticated=True, id=somebody_basket_id)
            self.response.assertStatusEqual(200)
            self.response.assertValueEqual('id', basket_id, 'Primary key value can not be changed.')
            self.response.assertValueEqual('status', 'Saved')

            # try to write to someone else's basket directly
            url = reverse('basket-detail', args=(somebody_basket_id,))
            self.response = self.put(url, status='Saved', session_id='admin', authenticated=True)
            self.response.assertStatusEqual(200)

            # try adding lines to someone elses basket
            line_data = {
                "basket": "http://testserver/api/baskets/%s/" % somebody_basket_id,
                "line_reference": "234_345",
                "product": "http://testserver/api/products/1/",
                "stockrecord": "http://testserver/api/stockrecords/1/",
                "quantity": 3,
                "price_currency": "EUR",
                "price_excl_tax": "100.0",
                "price_incl_tax": "121.0"
            }
            zurl = reverse('basket-lines-list', args=(basket_id,))
            self.response = self.post(zurl, session_id='admin', authenticated=True, **line_data)
            self.response.assertStatusEqual(406)

            # try to delete someone else's basket
            self.response = self.delete(url, session_id='admin', authenticated=True)
            self.response.assertStatusEqual(204)

    def test_add_product_anonymous(self):
        "Test if an anonymous user can add a product to his basket"
        self.response = self.post('api-basket-add-product', url="http://testserver/api/products/1/", quantity=5)
        self.response.assertStatusEqual(200)

        self.response = self.get(self.response['lines'])
        self.assertEqual(len(self.response.body), 1)
        line0 = self.response.body[0]
        self.assertEqual(line0['product'], "http://testserver/api/products/1/")
        self.assertEqual(line0['quantity'], 5)


    def test_add_product_authenticated(self):
        "Test if an authenticated user can add a product to his basket"
        self.login('nobody', 'nobody')
        self.response = self.post('api-basket-add-product', url="http://testserver/api/products/1/", quantity=5)
        self.response.assertStatusEqual(200)

        self.response = self.get(self.response['lines'])
        self.assertEqual(len(self.response.body), 1)
        line0 = self.response.body[0]
        self.assertEqual(line0['product'], "http://testserver/api/products/1/")
        self.assertEqual(line0['quantity'], 5)

    def test_basket_line_permissions(self):
        "A user's Basket lines can not be viewed by another user in any way (except admins)"
        self.login('nobody', 'nobody')
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        
        self.response = self.post('api-basket-add-product', url="http://testserver/api/products/1/", quantity=5)
        self.response = self.get(self.response['lines'])
        line0 = self.response.body[0]
        line0url = line0['url']

        self.response = self.get(line0url)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('product', "http://testserver/api/products/1/")
        self.response.assertValueEqual('quantity', 5)

        # now let's try to cheat
        self.login('somebody', 'somebody')
        self.response = self.get(line0url)
        self.response.assertStatusEqual(404)
        
        # admin can cheat, but he uses a different url
        line0id = re.search('(?P<id>\d+)/$', line0url).group('id')
        admin_line0url = reverse('line-detail', args=(line0id,))
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            self.login('admin', 'admin')
            self.response = self.get(admin_line0url)
            self.response.assertStatusEqual(200)

        # nobody can not cheat like admin
        self.login('somebody', 'somebody')
        self.response = self.get(admin_line0url)
        self.response.assertStatusEqual(403)

    def test_basket_line_permissions_header(self):
        "A user's Basket lines can not be viewed by another user in any way (except admins), even with header authetication"
        self.hlogin('nobody', 'nobody', session_id='nobody')
        self.response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(200)
        
        self.response = self.post('api-basket-add-product', url="http://testserver/api/products/1/", quantity=5, session_id='nobody', authenticated=True)
        self.response = self.get(self.response['lines'], session_id='nobody', authenticated=True)
        line0 = self.response.body[0]
        line0url = line0['url']

        self.response = self.get(line0url, session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('product', "http://testserver/api/products/1/")
        self.response.assertValueEqual('quantity', 5)

        # now let's try to cheat
        self.hlogin('somebody', 'somebody', session_id='somebody')
        self.response = self.get(line0url, session_id='somebody', authenticated=True)
        self.response.assertStatusEqual(404)

        # admin can cheat, but he uses a different url
        line0id = re.search('(?P<id>\d+)/$', line0url).group('id')
        admin_line0url = reverse('line-detail', args=(line0id,))
        with self.settings(OSCARAPI_BLOCK_ADMIN_API_ACCESS=False):
            self.hlogin('admin', 'admin', session_id='admin')
            self.response = self.get(admin_line0url, session_id='admin', authenticated=True)
            self.response.assertStatusEqual(200)

        # nobody can not cheat like admin
        self.login('somebody', 'somebody')
        self.response = self.get(admin_line0url)
        self.response.assertStatusEqual(403)

    def test_frozen_basket_can_not_be_accessed(self):
        "Prove that frozen baskets can nolonger be accessed by the user."
        self.login('nobody', 'nobody')
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('status', 'Open')

        # change status to saved
        url = reverse('basket-detail', args=(self.response['id'],))
        self.response = self.put(url, status='Frozen')
        self.response.assertValueEqual('status', 'Frozen')

        self.response = self.get(url)
        self.response.assertStatusEqual(403)

    def test_frozen_basket_can_not_be_accessed_header(self):
        "Prove that frozen baskets can nolonger be accessed by the user, even with header authentication"
        self.hlogin('nobody', 'nobody', session_id='nobody')
        self.response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('status', 'Open')

        # change status to saved
        url = reverse('basket-detail', args=(self.response['id'],))
        self.response = self.put(url, status='Frozen', session_id='nobody', authenticated=True)
        self.response.assertValueEqual('status', 'Frozen')

        self.response = self.get(url, session_id='nobody', authenticated=True)
        self.response.assertStatusEqual(403)

    def test_header_login_does_not_cause_regular_login(self):
        "Prove that there is not a bug in the test client that logs a user in when doing hlogin."
        self.hlogin('nobody', 'nobody', session_id='nobody')
        with self.settings(DEBUG=True):
            self.response = self.get('api-login')
            self.response.assertStatusEqual(204)
            self.response = self.get('api-login', session_id='nobody', authenticated=True)
            self.response.assertStatusEqual(200)
            self.response.assertValueEqual('username', 'nobody')

    def test_add_product_limit_basket(self):
        """Test if an anonymous user cannot add more than two products to his
            basket when amount of baskets is limited
        """
        settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = 2
        self.response = self.post(
            'api-basket-add-product',
            url="http://testserver/api/products/1/",
            quantity=3)
        self.response.assertStatusEqual(406)

    def test_total_prices_anonymous(self):
        "Test if the prices calcualted by the basket are ok"
        self.response = self.post(
            'api-basket-add-product',
            url="http://testserver/api/products/1/",
            quantity=5)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('total_incl_tax', '50.00')

    def test_add_product_above_stock(self):
        """Test if an anonymous user cannot add more products to his
            basket when stock is not sufficient
        """
        self.response = self.post(
            'api-basket-add-product',
            url="http://testserver/api/products/1/",
            quantity=25)
        self.response.assertStatusEqual(406)

    def test_adjust_basket_line_quantity(self):
        """Test if we can update the quantity of a line"""
        self.response = self.post(
            'api-basket-add-product',
            url="http://testserver/api/products/1/",
            quantity=5)
        self.response.assertStatusEqual(200)

        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)

        # Get the basket lines, and update the quantity to 4
        self.response = self.get(self.response['lines'])
        basket_line_url = self.response.data[0]['url']
        self.response = self.put(basket_line_url, quantity=4)
        self.response.assertStatusEqual(200)

        # see if it's updated
        self.response = self.get(basket_line_url)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('quantity', 4)
