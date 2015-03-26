from oscarapi.tests.utils import APITest
from django.core.urlresolvers import reverse


class SourceTypeTest(APITest):
    fixtures = ['sourcetype']

    def test_sourcetype_list(self):
        "Check if we get a list of source type with the default attributes"
        self.response = self.get('sourcetype-list')
        self.response.assertStatusEqual(200)
        # we should have two source type
        self.assertEqual(len(self.response.body), 2)
        # default we have 3 fields
        product = self.response.body[0]
        default_fields = ['url', 'name', 'code']
        for field in default_fields:
            self.assertIn(field, product)

    def test_sourcetype_detail(self):
        "Check source type details"
        self.response = self.get(reverse('sourcetype-detail', args=(1,)))
        self.response.assertStatusEqual(200)
        default_fields = ['url', 'name', 'code']
        for field in default_fields:
            self.assertIn(field, self.response.body)
        self.response.assertValueEqual('code', "paypal")
