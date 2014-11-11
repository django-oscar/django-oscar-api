import json
import unittest

from django.core.urlresolvers import reverse

from oscar.core.loading import get_model

from commerceconnect.tests.utils import APITest


Basket = get_model('basket', 'Basket')


class BasketTest(APITest):
    fixtures = [
        'product', 'productcategory', 'productattribute', 'productclass',
        'productattributevalue', 'category', 'attributeoptiongroup', 'attributeoption',
        'stockrecord', 'partner'
    ]
    def test_basket_api_create(self):
        "The basket api create command should work with regular cookie based login"
        url = reverse('basket-list')
        empty = Basket.objects.all()
        self.assertFalse(empty.exists(), "There should be no baskets yet.")

        # anonymous        
        data = {}

        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403, "Anonymous users can not use the basket api to create baskets.")

        # authenticated
        self.login('nobody', 'nobody')
        data = {'owner': "http://testserver%s" % reverse('user-detail', args=[2])}

        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403, "Authenticated regular users can not use the basket api to create baskets.")

        # admin
        self.login('admin', 'admin')

        data = {'owner': "http://testserver%s" % reverse('user-detail', args=[1])}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201, "It should be possible for a basket to be created, for a specific user.")

        data = json.loads(response.content)
        self.assertEqual(data['owner'], "http://testserver/commerceconnect/users/1/")

        data = {}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201, "It should be possible for a basket to be created for an anonymous user.")

        self.assertEqual(Basket.objects.count(), 2, "2 baskets should after creating 2 baskets.")

    def test_basket_api_create_header(self):
        "The basket api create command should work with header based login."
        empty = Basket.editable.all()
        self.assertFalse(empty.exists(), "There should be no baskets yet.")

        if self.hlogin('nobody', 'nobody', session_id='nobody'):
            response = self.post('basket-list', session_id='nobody', authenticated=True,
                owner="http://testserver%s" % reverse('user-detail', args=[2])
            )
            self.assertEqual(response.status_code, 403, "Authenticated regular users can not use the basket api to create baskets.")

        if self.hlogin('admin', 'admin', session_id='admin'):
            response = self.post('basket-list', session_id='admin', authenticated=True,
                owner="http://testserver%s" % reverse('user-detail', args=[1])
            )
            self.assertEqual(response.status_code, 201, "It should be possible for a basket to be created, for a specific user.")

            data = json.loads(response.content)
            self.assertEqual(data['owner'], "http://testserver/commerceconnect/users/1/")

        self.assertEqual(Basket.editable.count(), 3, "There should be 2 baskets from loging in and 1 is created with the api.")
            
    def test_retrieve_basket(self):
        "A user can fetch their own basket with the basket API and get's the same basket every time."
        # anonymous
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['owner'], None)
        basket_id = parsed_data['id']
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)
        
        # authenticated
        self.login('nobody', 'nobody')
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['owner'], "http://testserver/commerceconnect/users/2/")
        basket_id = parsed_data['id']
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)

        # admin
        with self.settings(CC_BLOCK_ADMIN_API_ACCESS=False):
            self.login('admin', 'admin')
            response = self.get('api-basket')
            self.assertEqual(response.status_code, 200)
            parsed_data = json.loads(response.content)
            self.assertEqual(parsed_data['owner'], "http://testserver/commerceconnect/users/1/")
            basket_id = parsed_data['id']
            response = self.get('api-basket')
            self.assertEqual(response.status_code, 200)
            parsed_data = json.loads(response.content)
            self.assertEqual(parsed_data['id'], basket_id)

        self.assertEqual(Basket.editable.count(), 3, "There should be 3 baskets open after 3 users accessed a basket.")

    def test_retrieve_basket_header(self):
        "Using header authentication the basket api should also work perfectly."
        # anonymous
        response = self.get('api-basket', session_id='anonymous')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['owner'], None)
        basket_id = parsed_data['id']
        response = self.get('api-basket', session_id='anonymous')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)
        
        # authenticated
        self.hlogin('nobody', 'nobody', session_id='nobody')
        response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['owner'], "http://testserver/commerceconnect/users/2/")
        basket_id = parsed_data['id']
        response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)

        # admin
        with self.settings(CC_BLOCK_ADMIN_API_ACCESS=False):
            self.hlogin('admin', 'admin', session_id='admin')
            response = self.get('api-basket', session_id='admin', authenticated=True)
            self.assertEqual(response.status_code, 200)
            parsed_data = json.loads(response.content)
            self.assertEqual(parsed_data['owner'], "http://testserver/commerceconnect/users/1/")
            basket_id = parsed_data['id']
            response = self.get('api-basket', session_id='admin', authenticated=True)
            self.assertEqual(response.status_code, 200)
            parsed_data = json.loads(response.content)
            self.assertEqual(parsed_data['id'], basket_id)

        self.assertEqual(Basket.editable.count(), 3, "There should be 3 baskets open after 3 users accessed a basket.")

    def test_basket_read_permissions(self):
        "A regular or anonymous user should not be able to fetch someone elses basket."
        # anonymous user can retrive a basket.
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)

        # try to access the urls in the response.
        parsed_data = json.loads(response.content)
        basket_url = parsed_data['url']
        basket_lines = parsed_data['lines']

        response = self.client.get(basket_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(basket_lines)
        self.assertEqual(response.status_code, 200)

        # create a basket for somebody else
        b = Basket.editable.create(owner_id=2)
        self.assertEqual(str(b.owner), 'nobody')
        self.assertEqual(b.pk, 2)

        # try to acces somebody else's basket (hihi).
        url = reverse('basket-detail', args=(2,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "Script kiddies should fail to collect other users carts.")
        url = reverse('basket-lines-list', args=(2,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "Script kiddies should fail to collect other users cart items.")

        # now try for authenticated user.
        self.login('nobody', 'nobody')
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)

        # try to access the urls in the response.
        parsed_data = json.loads(response.content)
        basket_url = parsed_data['url']
        basket_lines = parsed_data['lines']

        response = self.client.get(basket_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(basket_lines)
        self.assertEqual(response.status_code, 200)

        # try to acces somebody else's basket (hihi).
        url = reverse('basket-detail', args=(1,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "Script kiddies should fail to collect other users carts.")
        url = reverse('basket-lines-list', args=(1,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "Script kiddies should fail to collect other users cart items.")

        # now let's show the power of the admin!
        with self.settings(CC_BLOCK_ADMIN_API_ACCESS=False):
            self.login('admin', 'admin')
            response = self.get('api-basket')
            self.assertEqual(response.status_code, 200)

            # try to access the urls in the response.
            parsed_data = json.loads(response.content)
            basket_url = parsed_data['url']
            basket_lines = parsed_data['lines']

            response = self.client.get(basket_url)
            self.assertEqual(response.status_code, 200)

            response = self.client.get(basket_lines)
            self.assertEqual(response.status_code, 200)

            # try to acces somebody else's basket (hihi).
            url = reverse('basket-detail', args=(1,))
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "Staff users can access anything.")
            url = reverse('basket-lines-list', args=(1,))
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "Staff users can access anything.")

        self.assertEqual(Basket.editable.count(), 3, "There should be 3 baskets open after 3 users accessed a basket.")

    def test_basket_read_permissions_header(self):
        "A regular or anonymous user should not be able to fetch someone elses basket, even when authenticating with a session header."
        # anonymous user can retrieve a basket.
        response = self.get('api-basket', session_id='anonymous')
        self.assertEqual(response.status_code, 200)

        # try to access the urls in the response.
        parsed_data = json.loads(response.content)
        basket_url = parsed_data['url']
        basket_lines = parsed_data['lines']

        response = self.client.get(basket_url, HTTP_SESSION_ID='SID:ANON:testserver:anonymous')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(basket_lines, HTTP_SESSION_ID='SID:ANON:testserver:anonymous')
        self.assertEqual(response.status_code, 200)

        # create a basket for somebody else
        b = Basket.editable.create(owner_id=2)
        self.assertEqual(str(b.owner), 'nobody')
        self.assertEqual(b.pk, 2)

        # try to acces somebody else's basket (hihi).
        url = reverse('basket-detail', args=(2,))
        response = self.client.get(url, HTTP_SESSION_ID='SID:ANON:testserver:anonymous')
        self.assertEqual(response.status_code, 403, "Script kiddies should fail to collect other users carts.")
        url = reverse('basket-lines-list', args=(2,))
        response = self.client.get(url, HTTP_SESSION_ID='SID:ANON:testserver:anonymous')
        self.assertEqual(response.status_code, 403, "Script kiddies should fail to collect other users cart items.")

        # now try for authenticated user.
        self.hlogin('nobody', 'nobody', session_id='nobody')
        response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.assertEqual(response.status_code, 200)

        # try to access the urls in the response.
        parsed_data = json.loads(response.content)
        basket_url = parsed_data['url']
        basket_lines = parsed_data['lines']

        response = self.client.get(basket_url, HTTP_SESSION_ID='SID:AUTH:testserver:nobody')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(basket_lines, HTTP_SESSION_ID='SID:AUTH:testserver:nobody')
        self.assertEqual(response.status_code, 200)

        # try to acces somebody else's basket (hihi).
        url = reverse('basket-detail', args=(1,))
        response = self.client.get(url, HTTP_SESSION_ID='SID:AUTH:testserver:nobody')
        self.assertEqual(response.status_code, 403, "Script kiddies should fail to collect other users carts.")
        url = reverse('basket-lines-list', args=(1,))
        response = self.client.get(url, HTTP_SESSION_ID='SID:AUTH:testserver:nobody')
        self.assertEqual(response.status_code, 403, "Script kiddies should fail to collect other users cart items.")

        # now let's show the power of the admin!
        with self.settings(CC_BLOCK_ADMIN_API_ACCESS=False):
            self.hlogin('admin', 'admin', session_id='admin')
            response = self.get('api-basket', session_id='admin', authenticated=True)
            self.assertEqual(response.status_code, 200)

            # try to access the urls in the response.
            parsed_data = json.loads(response.content)
            basket_url = parsed_data['url']
            basket_lines = parsed_data['lines']

            response = self.client.get(basket_url, HTTP_SESSION_ID='SID:AUTH:testserver:admin')
            self.assertEqual(response.status_code, 200)

            response = self.client.get(basket_lines, HTTP_SESSION_ID='SID:AUTH:testserver:admin')
            self.assertEqual(response.status_code, 200)

            # try to acces somebody else's basket (hihi).
            url = reverse('basket-detail', args=(1,))
            response = self.client.get(url, HTTP_SESSION_ID='SID:AUTH:testserver:admin')
            self.assertEqual(response.status_code, 200, "Staff users can access anything.")
            url = reverse('basket-lines-list', args=(1,))
            response = self.client.get(url, HTTP_SESSION_ID='SID:AUTH:testserver:admin')
            self.assertEqual(response.status_code, 200, "Staff users can access anything.")

        self.assertEqual(Basket.editable.count(), 3, "There should be 3 baskets open after 3 users accessed a basket.")

    def test_basket_write_permissions_anonymous(self):
        "An anonymous user should not be able to change someone elses basket."

        # anonymous user
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)

        # try to access the urls in the response.
        parsed_data = json.loads(response.content)
        basket_id = parsed_data['id']
        basket_url = parsed_data['url']
        self.assertEqual(parsed_data['status'], 'Open')

        # change status to frozen
        url = reverse('basket-detail', args=(basket_id,))
        response = self.put(url, status='Saved')

        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)
        self.assertEqual(parsed_data['status'], 'Saved')

        # and back to open again
        response = self.put(url, status='Open')
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)
        self.assertEqual(parsed_data['status'], 'Open')

        # write a line to the basket
        line_data = {
            "basket": basket_url, 
            "line_reference": "234_345", 
            "product": "http://testserver/commerceconnect/products/1/", 
            "stockrecord": "http://testserver/commerceconnect/stockrecords/1/", 
            "quantity": 3, 
            "price_currency": "EUR", 
            "price_excl_tax": "100.0", 
            "price_incl_tax": "121.0",
        }
        line_url = reverse('basket-lines-list', args=(basket_id,))
        response = self.post(line_url, **line_data)
        self.assertEqual(response.status_code, 201)

        # throw the basket away
        response = self.delete(url)
        self.assertEqual(response.status_code, 204)

        # now lets start messing around
        response = self.get('api-basket')
        self.assertEqual(response.status_code, 200)
        basket_id = json.loads(response.content)['id']

        # create a basket for another user.
        b = Basket.editable.create(owner_id=2)
        self.assertEqual(str(b.owner), 'nobody')
        self.assertEqual(Basket.objects.count(), 2)
        nobody_basket_id = b.pk
        
        # try to access the urls in the response.
        parsed_data = json.loads(response.content)
        basket_id = parsed_data['id']
        basket_url = parsed_data['url']
        url = reverse('basket-detail', args=(basket_id,))

        self.assertEqual(parsed_data['status'], 'Open')

        # try to write to someone else's basket by sending the primary key
        # along.
        response = self.put(url, status='Frozen', id=nobody_basket_id)
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id, 'Primary key value can not be changed.')
        self.assertEqual(parsed_data['status'], 'Frozen')

        # try to write to someone else's basket directly
        url = reverse('basket-detail', args=(nobody_basket_id,))
        response = self.put(url, status='Frozen')
        self.assertEqual(response.status_code, 403)

        # try to delete someone else's basket
        response = self.delete(url)
        self.assertEqual(response.status_code, 403)
        
        # try adding lines to someone elses basket
        line_data = {
            "basket": "http://testserver/commerceconnect/baskets/%s/" % nobody_basket_id, 
            "line_reference": "234_345", 
            "product": "http://testserver/commerceconnect/products/1/", 
            "stockrecord": "http://testserver/commerceconnect/stockrecords/1/", 
            "quantity": 3, 
            "price_currency": "EUR", 
            "price_excl_tax": "100.0", 
            "price_incl_tax": "121.0"
        }
        url = reverse('basket-lines-list', args=(basket_id,))
        response = self.post(url, **line_data)
        self.assertEqual(response.status_code, 403)

    def test_basket_write_permissions_authenticated(self):
        "An authenticated user should not be able to change someone elses basket."

        # now try for authenticated user.
        self.hlogin('nobody', 'nobody', session_id='nobody')
        response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.assertEqual(response.status_code, 200)

        # try to access the urls in the response.
        parsed_data = json.loads(response.content)
        basket_id = parsed_data['id']
        basket_url = parsed_data['url']
        owner_url = parsed_data['owner']
        self.assertIn(reverse('user-detail', args=(2,)), owner_url)
        self.assertEqual(parsed_data['status'], 'Open')

        # change status to frozen
        url = reverse('basket-detail', args=(basket_id,))
        response = self.put(url, status='Saved', session_id='nobody', authenticated=True)

        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)
        self.assertEqual(parsed_data['status'], 'Saved')

        # and back to open again
        response = self.put(url, status='Open', session_id='nobody', authenticated=True)
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id)
        self.assertEqual(parsed_data['status'], 'Open')

        # write a line to the basket
        line_data = {
            "basket": basket_url, 
            "line_reference": "234_345", 
            "product": "http://testserver/commerceconnect/products/1/", 
            "stockrecord": "http://testserver/commerceconnect/stockrecords/1/", 
            "quantity": 3, 
            "price_currency": "EUR", 
            "price_excl_tax": "100.0", 
            "price_incl_tax": "121.0",
        }
        line_url = reverse('basket-lines-list', args=(basket_id,))
        response = self.post(line_url, session_id='nobody', authenticated=True, **line_data)
        self.assertEqual(response.status_code, 201)

        # throw the basket away
        response = self.delete(url, session_id='nobody', authenticated=True)
        self.assertEqual(response.status_code, 204)

        # now lets start messing around
        response = self.get('api-basket', session_id='nobody', authenticated=True)
        self.assertEqual(response.status_code, 200)
        basket_id = json.loads(response.content)['id']

        # create a basket for another user.
        b = Basket.editable.create(owner_id=3)
        self.assertEqual(str(b.owner), 'somebody')
        self.assertEqual(Basket.objects.count(), 2)
        somebody_basket_id = b.pk

        # try to access the urls in the response.
        parsed_data = json.loads(response.content)
        basket_id = parsed_data['id']
        basket_url = parsed_data['url']
        url = reverse('basket-detail', args=(basket_id,))

        self.assertEqual(parsed_data['status'], 'Open')

        # try to write to someone else's basket by sending the primary key
        # along.
        response = self.put(url, status='Frozen', id=somebody_basket_id)
        self.assertEqual(response.status_code, 200)
        parsed_data = json.loads(response.content)
        self.assertEqual(parsed_data['id'], basket_id, 'Primary key value can not be changed.')
        self.assertEqual(parsed_data['status'], 'Frozen')

        # try to write to someone else's basket directly
        url = reverse('basket-detail', args=(somebody_basket_id,))
        response = self.put(url, status='Frozen')
        self.assertEqual(response.status_code, 403)

        # try to delete someone else's basket
        response = self.delete(url)
        self.assertEqual(response.status_code, 403)

        # try adding lines to someone elses basket
        line_data = {
            "basket": "http://testserver/commerceconnect/baskets/%s/" % somebody_basket_id,
            "line_reference": "234_345",
            "product": "http://testserver/commerceconnect/products/1/",
            "stockrecord": "http://testserver/commerceconnect/stockrecords/1/",
            "quantity": 3,
            "price_currency": "EUR",
            "price_excl_tax": "100.0",
            "price_incl_tax": "121.0"
        }
        url = reverse('basket-lines-list', args=(basket_id,))
        response = self.post(url, **line_data)
        self.assertEqual(response.status_code, 403)
        
        ######################################################################
        # NEEDS TEST FOR ADMIN USER!!!                                       #
        ######################################################################

    @unittest.skip
    def test_basket_write_permissions_header(self):
        "A regular or anonymous user should not be able to change another user's basket, when authinticating with session header."
        self.fail("Needs tests for anonymous, authenticated and admin user, same test as in test_basket_write_permissions, but different authentication.")

    def test_add_product(self):
        "Test if an anonymous user can add a product to his basket"
        response = self.post('api-basket-add-product', url="http://testserver/commerceconnect/products/1/", quantity=5)
        self.assertEqual(response.status_code, 200)
    
    @unittest.skip
    def test_basket_line_permissions(self):
        "Prove that the sensitive information associated with basket lines, can not be viewed by another user in any way (except admins)"
        self.fail('not implemented')
