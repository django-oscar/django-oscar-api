import json
from django.conf import settings
from django.core.urlresolvers import reverse

from oscar.core.loading import get_model

from oscarapi.tests.utils import APITest


WishList = get_model('wishlists', 'WishList')


class WishListTest(APITest):
    fixtures = [
        'product', 'productcategory', 'productattribute', 'productclass',
        'productattributevalue', 'category', 'attributeoptiongroup', 'attributeoption',
        'stockrecord', 'partner'
    ]

    def test_wishlist_api_create(self):
        "The wishlist api create command should work with regular cookie based login"
        url = reverse('wishlist-list')
        empty = WishList.objects.all()
        self.assertFalse(empty.exists(), "There should be no wishlists yet.")

        # anonymous
        data = {}

        self.response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.response.assertStatusEqual(403, "Anonymous users can not use the wishlist api to create wishlists.")

        # authenticated
        self.login('nobody', 'nobody')
        data = {'owner': "http://testserver%s" % reverse('user-detail', args=[2])}

        self.response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.response.assertStatusEqual(403, "Authenticated regular users can not use the basket api to create baskets.")

        # admin
        self.login('admin', 'admin')

        data = {'owner': "http://testserver%s" % reverse('user-detail', args=[1])}
        self.response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.response.assertStatusEqual(405, "It shouldn't be possible for a wishlist to be created, for a specific user.")

        data = {}
        self.response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.response.assertStatusEqual(405, "It shouldn't be possible for a wishlist to be created for an anonymous user.")
        self.assertEqual(WishList.objects.count(), 0, "0 wishlists should after creating 2 wishlistss.")

    def test_retrieve_wishlist(self):
        "A user can fetch their own wishlist with the wishlist API and get's the same wishlist every time."
        # anonymous
        self.response = self.get('api-wishlist')
        self.response.assertStatusEqual(403)

        # authenticated
        self.login('nobody', 'nobody')
        self.response = self.get('api-wishlist')
        self.response.assertStatusEqual(200)
        self.response.assertObjectIdEqual('owner', 2)
        wishlist_id = self.response['id']

        self.response = self.get('api-wishlist')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', wishlist_id)

        self.login('admin', 'admin')
        self.response = self.get('api-wishlist')
        self.response.assertStatusEqual(200)
        self.response.assertObjectIdEqual('owner', 1)
        wishlist_id = self.response['id']

        self.response = self.get('api-wishlist')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', wishlist_id)

        self.assertEqual(WishList.objects.count(), 2, "There should be 2 wishlists open after 2 users accessed a wishlist.")

    def test_wishlists_read_permissions(self):
        "A regular or anonymous user should not be able to fetch someone elses basket."
        # anonymous user can retrive a wishlist.
        self.response = self.get('api-wishlist')
        self.response.assertStatusEqual(403)

        # create a wishlist for somebody else
        b = WishList.objects.create(owner_id=2)
        self.assertEqual(str(b.owner), 'nobody')
        self.assertEqual(b.pk, 1)

        # try to acces somebody else's wishlist (hihi).
        url = reverse('wishlist-detail', args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users carts.")
        url = reverse('wishlist-lines-list', args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users cart items.")

        # now try for authenticated user.
        self.login('nobody', 'nobody')
        self.response = self.get('api-wishlist')
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response['url']
        basket_lines = self.response['lines']

        self.response = self.client.get(basket_url)
        self.response.assertStatusEqual(200)

        self.response = self.client.get(basket_lines)
        self.response.assertStatusEqual(200)

        # try to acces somebody else's wishlist.
        self.login('somebody', 'somebody')
        url = reverse('wishlist-detail', args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users carts.")

        url = reverse('wishlist-lines-list', args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users cart items.")

        # now let's show the power of the admin!
        self.login('admin', 'admin')
        self.response = self.get('api-wishlist')
        self.response.assertStatusEqual(200)

        # try to access the urls in the response.
        basket_url = self.response['url']
        basket_lines = self.response['lines']

        self.response = self.client.get(basket_url)
        self.response.assertStatusEqual(200)

        self.response = self.client.get(basket_lines)
        self.response.assertStatusEqual(200)

        # try to acces somebody else's wishlist (hihi).
        url = reverse('wishlist-detail', args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(200, "Staff users can access anything.")

        url = reverse('wishlist-lines-list', args=(1,))
        self.response = self.client.get(url)
        self.response.assertStatusEqual(200, "Staff users can access anything.")

        self.assertEqual(WishList.objects.count(), 2, "There should be 2 wishlists open after 2 users accessed a wishlist.")

    def test_add_product(self):

        data = {
            "url": "http://testserver.org/api/products/1/",
        }

        # anonymous
        self.response = self.post('api-wishlist-add-product', **data)
        self.response.assertStatusEqual(403)

        # nobody
        self.login('nobody', 'nobody')
        self.response = self.get('api-wishlist')
        self.response.assertStatusEqual(200)

        self.response = self.post('api-wishlist-add-product', **data)
        self.response.assertStatusEqual(200)

        lines_url = self.response.body['lines']

        self.response = self.get(lines_url)
        self.response.assertStatusEqual(200)

        self.assertEqual(len(self.response.body), 1)

        data = {
            "url": "http://testserver.org/api/products/150/",
        }

        self.response = self.post('api-wishlist-add-product', **data)
        self.response.assertStatusEqual(406)

        self.response = self.get('api-wishlist')
        self.response.assertStatusEqual(200)

        lines_url = self.response.body['lines']

        self.response = self.get(lines_url)
        self.response.assertStatusEqual(200)

        self.assertEqual(len(self.response.body), 1)

    def test_add_to_basket(self):
        data = {
            "url": "http://testserver.org/api/wishlistlines/33/",
        }
        # anonymous
        self.response = self.post('api-wishlist-add-to-basket', **data)
        self.response.assertStatusEqual(403)

        data = {
            "url": "http://testserver.org/api/products/1/",
        }

        # nobody
        self.login('nobody', 'nobody')
        self.response = self.get('api-wishlist')
        self.response.assertStatusEqual(200)
        lines_url = self.response.body['lines']

        self.response = self.post('api-wishlist-add-product', **data)
        self.response.assertStatusEqual(200)

        self.response = self.get(lines_url)
        self.response.assertStatusEqual(200)

        self.assertEqual(len(self.response.body), 1)

        data = {
            "url": "http://testserver.org/api/wishlistlines/33/",
        }
        self.response = self.post('api-wishlist-add-to-basket', **data)
        self.response.assertStatusEqual(406)

        self.response = self.get(lines_url)
        self.response.assertStatusEqual(200)

        self.assertEqual(len(self.response.body), 1)

        data = {
            "url": self.response.body[0]['url']
        }

        self.response = self.post('api-wishlist-add-to-basket', **data)
        self.response.assertStatusEqual(200)

        self.response = self.get(lines_url)
        self.response.assertStatusEqual(200)

        self.assertEqual(len(self.response.body), 0)
