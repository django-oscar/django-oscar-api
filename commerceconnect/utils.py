import oscar.models.fields
from django.conf import settings
from rest_framework import serializers


def overridable(name, default):
    """
    Seems useless but this is for readability
    """
    return getattr(settings, name, default)

class OscarSerializer(object):
    field_mapping = dict(serializers.ModelSerializer.field_mapping, **{
        oscar.models.fields.NullCharField: serializers.CharField
    })
    
    def to_native(self, obj):
        num_fields = len(self.get_fields())
        native = super(OscarSerializer, self).to_native(obj)

        if num_fields == 1:
            _, val = next(native.iteritems())
            return val
        
        return native
    
class OscarModelSerializer(OscarSerializer, serializers.ModelSerializer):
    """
    Correctly map oscar fields to serializer fields.
    """
    
class OscarHyperlinkedModelSerializer(OscarSerializer, serializers.HyperlinkedModelSerializer):
    """
    Correctly map oscar fields to serializer fields.
    """


def get_domain(request):
    return request.get_host().split(':')[0]