from django.db import models
from django.test import TestCase
from rest_framework.fields import ImageField
from oscarapi.utils.loading import get_api_class

ImageUrlField = get_api_class("serializers.fields", "ImageUrlField")


class SerializerstTest(TestCase):
    def test_drf_image_field_is_not_monkey_patched(self):
        # see https://github.com/django-oscar/django-oscar-api/issues/287
        from rest_framework.serializers import ModelSerializer

        default_image_field = ModelSerializer.serializer_field_mapping[
            models.ImageField
        ]

        self.assertEqual(default_image_field, ImageField)
        self.assertNotEqual(default_image_field, ImageUrlField)
