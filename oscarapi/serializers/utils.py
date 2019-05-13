from rest_framework import serializers
import oscar.models.fields


def expand_field_mapping(extra_fields):
    # This doesn't make a copy
    field_mapping = serializers.ModelSerializer.serializer_field_mapping
    field_mapping.update(extra_fields)
    return field_mapping


class OscarSerializer(object):
    field_mapping = expand_field_mapping({
        oscar.models.fields.NullCharField: serializers.CharField
    })

    def __init__(self, *args, **kwargs):
        """
        Allow the serializer to be initiated with only a subset of the
        speccified fields
        """
        fields = kwargs.pop('fields', None)
        super(OscarSerializer, self).__init__(*args, **kwargs)
        if fields:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class OscarModelSerializer(OscarSerializer, serializers.ModelSerializer):
    """
    Correctly map oscar fields to serializer fields.
    """


class OscarHyperlinkedModelSerializer(
        OscarSerializer, serializers.HyperlinkedModelSerializer):
    """
    Correctly map oscar fields to serializer fields.
    """
