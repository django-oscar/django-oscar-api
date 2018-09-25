from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.test import RequestFactory, TestCase

from oscarapi.middleware import ApiGatewayMiddleWare
from oscarapi.models import ApiKey


class ApiGatewayMiddleWareTest(TestCase):

    rf = RequestFactory()

    def setUp(self):
        super(ApiGatewayMiddleWareTest, self).setUp()

        ApiKey.objects.create(key='testapikey')

    def tearDown(self):
        ApiKey.objects.filter(key='testapikey').delete()

        super(ApiGatewayMiddleWareTest, self).tearDown()

    def test_process_request(self):
        basket_url = reverse('api-basket')

        # without Authorization header
        request = self.rf.get(basket_url)
        with self.assertRaises(PermissionDenied):
            ApiGatewayMiddleWare().process_request(request)

        # invalid Authorization header
        request = self.rf.get(basket_url, HTTP_AUTHORIZATION='wrongkey')
        with self.assertRaises(PermissionDenied):
            ApiGatewayMiddleWare().process_request(request)

        # valid Authorization header
        request = self.rf.get(basket_url, HTTP_AUTHORIZATION='testapikey')
        self.assertIsNone(ApiGatewayMiddleWare().process_request(request))
