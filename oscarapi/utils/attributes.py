import operator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import MISSING_ERROR_MESSAGE
from rest_framework.exceptions import ErrorDetail
from oscarapi.utils.loading import get_api_class
from oscarapi.serializers import fields as oscarapi_fields

attribute_details = operator.itemgetter("code", "value")
entity_internal_value = get_api_class("serializers.hooks", "entity_internal_value")


class AttributeFieldBase:
    default_error_messages = {
        "no_such_option": _("{code}: Option {value} does not exist."),
        "invalid": _("Wrong type, {error}."),
        "attribute_validation_error": _(
            "Error assigning `{value}` to {code}, {error}."
        ),
        "attribute_required": _("Attribute {code} is required."),
        "attribute_missing": _(
            "No attribute exist with code={code}, "
            "please define it in the product_class first."
        ),
        "child_without_parent": _(
            "Can not find attribute if product_class is empty and "
            "parent is empty as well, child without parent?"
        ),
    }

    def to_attribute_type_value(self, attribute, code, value):
        internal_value = value
        # pylint: disable=no-member
        if attribute.required and value is None:
            self.fail("attribute_required", code=code)

        # some of these attribute types need special processing, or their
        # validation will fail
        if attribute.type == attribute.OPTION:
            internal_value = attribute.option_group.options.get(option=value)
        elif attribute.type == attribute.MULTI_OPTION:
            if attribute.required and not value:
                self.fail("attribute_required", code=code)
            internal_value = attribute.option_group.options.filter(option__in=value)
            if len(value) != internal_value.count():
                non_existing = set(value) - set(
                    internal_value.values_list("option", flat=True)
                )
                non_existing_as_error = ",".join(sorted(non_existing))
                self.fail("no_such_option", value=non_existing_as_error, code=code)
        elif attribute.type == attribute.DATE:
            date_field = serializers.DateField()
            internal_value = date_field.to_internal_value(value)
        elif attribute.type == attribute.DATETIME:
            date_field = serializers.DateTimeField()
            internal_value = date_field.to_internal_value(value)
        elif attribute.type == attribute.ENTITY:
            internal_value = entity_internal_value(attribute, value)
        elif attribute.type in [attribute.IMAGE, attribute.FILE]:
            image_field = oscarapi_fields.ImageUrlField()
            # pylint: disable=protected-access
            image_field._context = self.context
            internal_value = image_field.to_internal_value(value)

        return internal_value


class AttributeConverter(AttributeFieldBase):
    def __init__(self, context):
        self.context = context
        self.errors = []

    def fail(self, key, **kwargs):
        """
        An implementation of fail that collects errors instead of raising them
        """
        try:
            msg = self.default_error_messages[key]
        except KeyError:
            class_name = self.__class__.__name__
            msg = MISSING_ERROR_MESSAGE.format(class_name=class_name, key=key)
            raise AssertionError(msg)
        message_string = msg.format(**kwargs)
        self.errors.append(ErrorDetail(message_string, code=key))
