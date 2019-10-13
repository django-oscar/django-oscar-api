from django.test import TestCase
from oscar.core.loading import get_model
from oscarapi.utils import exists

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


class UtilsExistTest(TestCase):
    fixtures = [
        "product",
        "productcategory",
        "productattribute",
        "productclass",
        "productattributevalue",
        "category",
        "attributeoptiongroup",
        "attributeoption",
        "stockrecord",
        "partner",
        "option",
    ]

    def _test_construct_id_filter(self, model, data):

        query = exists.construct_id_filter(model, data)
        qs = model.objects.filter(query)
        self.assertEqual(qs.count(), 1)
        p = qs.first()
        return p

    def test_product_construct_id_filter_pk(self):
        for pk in [1, 2, 3, 4]:
            p = self._test_construct_id_filter(Product, {"id": pk, "title": "klaas"})
            self.assertEqual(p.id, pk)

    def test_category_construct_id_filter_pk(self):
        c = self._test_construct_id_filter(Category, {"id": 1, "name": "zult"})
        self.assertEqual(c.id, 1)

    def test_product_construct_id_filter_upc(self):
        for upc in ["1234", "child-1234", "attrtypestest", "entity"]:
            p = self._test_construct_id_filter(Product, {"upc": upc, "title": "henk"})
            self.assertEqual(p.upc, upc)

    def test_product_attribute_value_construct_id_filter_unique_together(self):
        av = self._test_construct_id_filter(
            ProductAttributeValue, {"attribute": 1, "product": 1, "value_text": "klaas"}
        )
        self.assertEqual(av.id, 1)
