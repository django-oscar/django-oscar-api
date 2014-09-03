import oscar.models.fields
from django.conf import settings
from rest_framework import serializers


def overridable(name, default):
    """
    Seems useless but this is for readability
    """
    return getattr(settings, name, default)


class OscarModelSerializer(serializers.ModelSerializer):
    """
    Correctly map oscar fields to serializer fields.
    """
    field_mapping = dict(serializers.ModelSerializer.field_mapping, **{
        oscar.models.fields.NullCharField: serializers.CharField
    })

def get_domain(request):
    return request.get_host().split(':')[0]