import logging
from django.db import models
from django.db.models.manager import Manager
from django.db.models.constants import LOOKUP_SEP

from rest_framework import serializers

import oscar.models.fields

from oscarapi.utils.exists import construct_id_filter
from .fields import ImageUrlField

logger = logging.getLogger(__name__)


def expand_field_mapping(extra_fields):
    # This doesn't make a copy
    field_mapping = serializers.ModelSerializer.serializer_field_mapping
    field_mapping.update(extra_fields)
    return field_mapping


class OscarSerializer(object):
    field_mapping = expand_field_mapping(
        {
            oscar.models.fields.NullCharField: serializers.CharField,
            models.ImageField: ImageUrlField,
        }
    )

    def __init__(self, *args, **kwargs):
        """
        Allow the serializer to be initiated with only a subset of the
        specified fields
        """
        fields = kwargs.pop("fields", None)
        super(OscarSerializer, self).__init__(*args, **kwargs)
        if fields:
            allowed = set(fields)
            existing = set(self.fields.keys())  # pylint: disable=no-member
            for field_name in existing - allowed:
                self.fields.pop(field_name)  # pylint: disable=no-member

    def update_relation(self, name, manager, values):
        if values is None:
            return

        serializer = self.fields[name]  # pylint: disable=no-member

        # use the serializer to update the attribute_values
        updated_values = serializer.update(manager, values)

        if self.partial:  # pylint: disable=no-member
            manager.add(*updated_values)
        elif hasattr(manager, "field") and not manager.field.null:
            # add the updated_attribute_values to the instance
            manager.add(*updated_values)
            # remove all the obsolete attribute values, this could be caused by
            # the product class changing for example, lots of attributes would become
            # obsolete.
            current_pks = [p.pk for p in updated_values]
            manager.exclude(pk__in=current_pks).delete()
        else:
            manager.set(updated_values)


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

        intermediate_result = manager.filter(automatic_filter)
        try:
            return intermediate_result.distinct().get()
        except manager.model.DoesNotExist:
            pass
        except manager.model.MultipleObjectsReturned as e:
            logger.error("Multiple objects on unique constrained items, freaky %s", e)
            logger.exception(e)

        # fallback to manually specified lookup_fields
        for lookup_field in self.Meta.lookup_fields:
            if lookup_field in datum:
                try:
                    return intermediate_result.get(
                        **{lookup_field: datum[lookup_field]}
                    )
                except manager.model.DoesNotExist:
                    continue
                except manager.model.MultipleObjectsReturned:
                    continue

        return None

    def get_name_and_rel_instance(self, manager):
        return manager.field.name, manager.instance

    def update(self, instance, validated_data):
        assert isinstance(instance, Manager)

        field_name, rel_instance = self.get_name_and_rel_instance(instance)

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


class UpdateForwardManyToManySerializer(UpdateListSerializer):
    def select_existing_item(self, manager, datum):
        # with manytomany there is no point in restricting the queryset
        # to the parent, because it is actually MEANT to share instances.
        return super(UpdateForwardManyToManySerializer, self).select_existing_item(
            manager.model.objects, datum
        )

    def get_name_and_rel_instance(self, manager):
        return manager.source_field_name, manager.instance
