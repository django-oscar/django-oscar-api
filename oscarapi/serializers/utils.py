from functools import wraps
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


class wrap_in_dict(object):
    """
    Wraps the return value in a dict
    
    >>> func = wrap_in_dict("henk")(str)
    >>> func(1)
    {'henk': '1'}
    >>> class Calc:
    ...     @wrap_in_dict("lmao")
    ...     def hoela(self, ugh):
    ...         return ugh + 1
    >>> calc = Calc()
    >>> calc.hoela(17)
    {'lmao': 18}
    """
    def __init__(self, key):
        self.key = key

    def __call__(self, func):
        @wraps(func)
        def _wrapped_in_dict(*args, **kwargs):
            return {self.key: func(*args, **kwargs)}

        return _wrapped_in_dict
