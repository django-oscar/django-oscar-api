from django.db import models
from django.db.models.manager import Manager
from django.db.models.constants import LOOKUP_SEP

from rest_framework import serializers

import oscar.models.fields


def expand_field_mapping(extra_fields):
    # This doesn't make a copy
    field_mapping = serializers.ModelSerializer.serializer_field_mapping
    field_mapping.update(extra_fields)
    return field_mapping


class OscarSerializer(object):
    field_mapping = expand_field_mapping(
        {oscar.models.fields.NullCharField: serializers.CharField}
    )

    def __init__(self, *args, **kwargs):
        """
        Allow the serializer to be initiated with only a subset of the
        speccified fields
        """
        fields = kwargs.pop("fields", None)
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
    OscarSerializer, serializers.HyperlinkedModelSerializer
):
    """
    Correctly map oscar fields to serializer fields.
    """


class DelayUniqueSerializerMixin(object):
    def get_unique_together_validators(self):
        validators = super(
            DelayUniqueSerializerMixin, self
        ).get_unique_together_validators()

        if self.parent is not None:
            for validator in validators:
                validator.queryset = self.parent.restrict_query_to_parent(
                    validator.queryset
                )

        return validators


class UpdateListSerializer(serializers.ListSerializer):
    """
    This serializer can be used to implement updates to nested serializers.
    
    It will try to match existing objects based on the presence of a primary
    key in the submitted data, or the fields specified by name in ``Meta.lookup_fields``
    """

    class Meta:
        lookup_fields = []

    def restrict_query_to_parent(self, query):
        ParentModelClass = self.parent.Meta.model
        relation_field = ParentModelClass._meta.get_field(self.field_name)

        parent_field_name = relation_field.field.name

        if self.parent.instance:
            return query.exclude(**{parent_field_name: self.parent.instance})
        else:
            parent_filter = construct_id_filter(
                ParentModelClass,
                self.parent.get_initial(),
                prefix="%s%s" % (parent_field_name, LOOKUP_SEP),
            )
            return query.exclude(parent_filter).distinct()

    def select_existing_item(self, manager, datum):
        automatic_filter = construct_id_filter(manager.model, datum)

        try:
            intermediate_result = manager.filter(automatic_filter)
            return intermediate_result.distinct().get()
        except manager.model.DoesNotExist:
            pass
        except manager.model.MultipleObjectsReturned as e:
            logger.error("Multiple objects on unique contrained items, freaky %s" % e)
            logger.exception(e)

        # fallback to manually specified lookup_fields
        for lookup_field in self.Meta.lookup_fields:
            if lookup_field in datum:
                try:
                    return manager.get(**{lookup_field: datum[lookup_field]})
                except manager.model.DoesNotExist:
                    continue
                except manager.model.MultipleObjectsReturned:
                    continue

        return None

    def update(self, instance, validated_data):
        assert isinstance(instance, Manager)

        field_name = instance.field.name
        rel_instance = instance.instance

        items = []
        for validated_datum in validated_data:
            complete_validated_datum = {field_name: rel_instance}
            complete_validated_datum.update(validated_datum)
            existing_item = self.select_existing_item(
                instance, complete_validated_datum
            )

            if existing_item is not None:
                updated_instance = self.child.update(
                    existing_item, complete_validated_datum
                )
            else:
                updated_instance = self.child.create(complete_validated_datum)

            items.append(updated_instance)

        return items


def _field_name(name, prefix=None):
    """
    Util for quick prefixes
    
    >>> _field_name(1)
    '1'
    >>> _field_name("henk")
    'henk'
    >>> _field_name("henk", 1)
    '1henk'
    """
    if prefix is None:
        return str(name)
    return "%s%s" % (prefix, name)


def construct_id_filter(model, data, prefix=None):
    """
    This function will construct a filter that can be used to uniquely
    identify an object based on the keys present in the data object.
    
    So if there are multiple fields on a model that are marked as unique, or
    the model has unique_together specifucations, all these can be used to
    uniquely identify the instance that represents the data.
    """
    _filter = models.Q()

    for unique_together in model._meta.unique_together:
        _filter |= models.Q(
            **{_field_name(key, prefix): data.get(key) for key in unique_together}
        )

    for field in model._meta.concrete_fields:
        if field.unique and field.name in data:
            _filter |= model.Q(**{_field_name(field.name, prefix): data[field.name]})

    return _filter
