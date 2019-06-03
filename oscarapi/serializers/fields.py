import logging
import operator

from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers, relations
from rest_framework.fields import get_attribute

from oscar.core.loading import get_model, get_class

from .exceptions import FieldError

logger = logging.getLogger(__name__)
ProductAttribute = get_model("catalogue", "ProductAttribute")
Category = get_model("catalogue", "Category")
create_from_breadcrumbs = get_class("catalogue.categories", "create_from_breadcrumbs")
attribute_details = operator.itemgetter("code", "value")


class TaxIncludedDecimalField(serializers.DecimalField):
    def __init__(self, excl_tax_field=None, excl_tax_value=None, **kwargs):
        self.excl_tax_field = excl_tax_field
        self.excl_tax_value = excl_tax_value
        super(TaxIncludedDecimalField, self).__init__(**kwargs)

    def get_attribute(self, instance):
        if instance.is_tax_known:
            return super(TaxIncludedDecimalField, self).get_attribute(instance)
        if self.excl_tax_field:
            return get_attribute(instance, (self.excl_tax_field,))
        return self.excl_tax_value


class DrillDownHyperlinkedIdentityField(relations.HyperlinkedIdentityField):
    def __init__(self, *args, **kwargs):
        try:
            self.extra_url_kwargs = kwargs.pop("extra_url_kwargs")
        except KeyError:
            msg = (
                "DrillDownHyperlinkedIdentityField requires 'extra_url_kwargs' argument"
            )
            raise ValueError(msg)

        super(DrillDownHyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def get_extra_url_kwargs(self, obj):
        return {
            key: operator.attrgetter(path)(obj)
            for key, path in self.extra_url_kwargs.items()
        }

    def get_url(
        self, obj, view_name, request, format
    ):  # pylint: disable=redefined-builtin
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        if hasattr(obj, "pk") and obj.pk in (None, ""):
            return None

        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {self.lookup_url_kwarg: lookup_value}
        kwargs.update(self.get_extra_url_kwargs(obj))
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class AttributeValueField(serializers.Field):
    """
    This field is used to handle the value of the ProductAttributeValue model
    
    Because the value is dependant on the type of the corresponding attribute,
    it is not fixed. This field solves the problem of handling the different
    types.
    """

    def __init__(self, **kwargs):
        # this field always needs the full object
        kwargs["source"] = "*"
        kwargs["error_messages"] = {
            "no_such_option": _("Option {value} does not exist."),
            "invalid": _("Wrong type, {error}."),
            "attribute_missing": _(
                "No attribute exist named {name} with code={code}, "
                "please define it in the product_class first."
            ),
        }
        super(AttributeValueField, self).__init__(**kwargs)

    def get_value(self, dictionary):
        # return all the data because this field uses everything
        return dictionary

    def to_internal_value(self, data):
        assert "product" in data or "product_class" in data

        try:
            code, value = attribute_details(data)
            internal_value = value

            if "product" in data:
                # we need the attribute to determine the type of the value
                attribute = ProductAttribute.objects.get(
                    code=code, product_class__products__id=data["product"]
                )
            elif "product_class" in data:
                attribute = ProductAttribute.objects.get(
                    code=code, product_class__slug=data.get("product_class")
                )

            if attribute.required and value is None:
                self.fail("required")

            # some of these attribute types need special processing, or their
            # validation will fail
            if attribute.type == attribute.OPTION:
                internal_value = attribute.option_group.options.get(option=value)
            elif attribute.type == attribute.MULTI_OPTION:
                if attribute.required and not value:
                    self.fail("required")
                internal_value = attribute.option_group.options.filter(option__in=value)
                if len(value) != internal_value.count():
                    non_existing = set(value) - set(
                        internal_value.values_list("option", flat=True)
                    )
                    non_existing_as_error = ",".join(sorted(non_existing))
                    self.fail("no_such_option", value=non_existing_as_error)
            elif attribute.type == attribute.DATE:
                date_field = serializers.DateField()
                internal_value = date_field.to_internal_value(value)
            elif attribute.type == attribute.DATETIME:
                date_field = serializers.DateTimeField()
                internal_value = date_field.to_internal_value(value)
            elif attribute.type == attribute.ENTITY:
                raise NotImplementedError(
                    "Writable Entity support requires a manual implementation, "
                    "because it is not possible to guess how the value "
                    "sent should be interpreted"
                )

            # the rest of the attribute types don't need special processing
            try:
                attribute.validate_value(internal_value)
            except TypeError as e:
                self.fail("invalid", error=e)

            return {"value": internal_value, "attribute": attribute}
        except ProductAttribute.DoesNotExist:  # maybe this is fatal I don;t know yet
            self.fail("attribute_missing", **data)
        except ObjectDoesNotExist as e:
            self.fail("no_such_option", value=value)
        except KeyError as e:
            field_name, = e.args
            raise FieldError(
                detail={field_name: self.error_messages["required"]}, code="required"
            )

    def to_representation(self, value):
        obj_type = value.attribute.type
        if obj_type == value.attribute.OPTION:
            return value.value.option
        elif obj_type == value.attribute.MULTI_OPTION:
            return value.value.values_list("option", flat=True)
        elif obj_type == value.attribute.FILE:
            return value.value.url
        elif obj_type == value.attribute.IMAGE:
            return value.value.url
        elif obj_type == value.attribute.ENTITY:
            if hasattr(value.value, "json"):
                return value.value.json()
            else:
                return _(
                    "%(entity)s has no json method, can not convert to json"
                    % {"entity": repr(value.value)}
                )

        # return the value as stored on ProductAttributeValue in the correct type
        return value.value


class CategoryField(serializers.RelatedField):
    def __init__(self, **kwargs):
        kwargs["queryset"] = Category.objects
        super(CategoryField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        return create_from_breadcrumbs(data)

    def to_representation(self, value):
        return value.full_name
