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
    """
    Attempts to find an existing AttributeOptionGroup with the given name
    and exactly the same set of options.

    Parameters:
        name (str): The name of the option group to look for.
        options (list): A list of option inputs, each of which must be either:
            - A dict with an "option" key, e.g., {"option": "Large"}
            - An AttributeOption instance

    Returns:
        AttributeOptionGroup instance if an exact match is found, otherwise None.
    """
    normalized_options = []
    for opt in options:
        if isinstance(opt, dict):
            if "option" not in opt:
                raise ValueError(f"Missing 'option' key in dict: {opt}")
            normalized_options.append(opt)
        elif hasattr(opt, "option"):
            # normalize AttributeOption instances
            normalized_options.append({"option": opt.option})
        else:
            raise TypeError(
                f"Invalid option type: {type(opt).__name__}. Expected dict or AttributeOption instance."
            )

    option_values = [opt["option"] for opt in normalized_options]
    query = (
        AttributeOptionGroup.objects.filter(name=name)
        .filter(options__option__in=option_values)
        .annotate(options_count=models.Count("options", distinct=True))
        .filter(options_count=len(option_values))
    )

    for q in query:
        try:
            # Compare sorted option lists; fallback if non-comparable types
            if sorted(list(q.options.values_list("option", flat=True))) == sorted(
                list(option_values)
            ):
                return q
        except TypeError:
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
