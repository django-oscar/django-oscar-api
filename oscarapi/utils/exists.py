"""
This module contains functions that can be used to identify an existing piece
of data in the database based on it's unique attributes
"""
from django.db import models

from oscar.core.loading import get_model

from .accessors import destructure

AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
Category = get_model("catalogue", "Category")


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
        if field.unique and field.name in data and data[field.name] is not None:
            _filter |= models.Q(**{_field_name(field.name, prefix): data[field.name]})

    return _filter


def find_existing_attribute_option_group(name, options):
    query = (
        AttributeOptionGroup.objects.filter(name=name)
        .annotate(options_count=models.Count("options"))
        .filter(options_count=len(options))
    )
    for option in options:
        query = query.filter(options__option=option)

    try:
        return query.get()
    except (
        AttributeOptionGroup.DoesNotExist,
        AttributeOptionGroup.MultipleObjectsReturned,
    ):
        return None


def bound_unique_together_get_or_create(bound_queryset, datum):
    QuerySetModel = bound_queryset.model
    if isinstance(datum, QuerySetModel):
        return datum

    keys = set(datum.keys())
    for unique_pair in QuerySetModel._meta.unique_together:
        overlap = keys & set(unique_pair)
        # one of the items in the unique specification should be already
        # bound in the queryset (used in a filter). So we need to look
        # for a unique spec that has overlap with the data keys, but has 1
        # key missing (which is the bound key)
        if overlap and len(overlap) >= (len(unique_pair) - 1):
            unbound_keys = list(overlap)
            lookups = destructure(datum, *unbound_keys)
            item, _ = bound_queryset.get_or_create(**lookups)
            return item

    return None


def bound_unique_together_get_or_create_multiple(bound_queryset, data):
    return [bound_unique_together_get_or_create(bound_queryset, date) for date in data]
