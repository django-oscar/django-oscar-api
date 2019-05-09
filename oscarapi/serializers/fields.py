import logging
import operator

from django.urls import NoReverseMatch
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers, relations
from rest_framework.reverse import reverse
from rest_framework.fields import get_attribute

from oscar.core.loading import get_model

from .utils import wrap_in_dict

logger = logging.getLogger(__name__)
ProductAttribute = get_model('catalogue', 'ProductAttribute')
attribute_details = operator.itemgetter("product", "code", "value")


class TaxIncludedDecimalField(serializers.DecimalField):
    def __init__(self, excl_tax_field=None, excl_tax_value=None,
                 *args, **kwargs):
        self.excl_tax_field = excl_tax_field
        self.excl_tax_value = excl_tax_value
        super(TaxIncludedDecimalField, self).__init__(*args, **kwargs)

    def get_attribute(self, instance):
        if instance.is_tax_known:
            return super(TaxIncludedDecimalField, self).get_attribute(instance)
        if self.excl_tax_field:
            return get_attribute(instance, (self.excl_tax_field, ))
        return self.excl_tax_value


class DrillDownHyperlinkedIdentityField(relations.HyperlinkedIdentityField):
    def __init__(self, *args, **kwargs):
        try:
            self.extra_url_kwargs = kwargs.pop('extra_url_kwargs')
        except KeyError:
            msg = "DrillDownHyperlinkedIdentityField requires 'extra_url_kwargs' argument"
            raise ValueError(msg)

        super(DrillDownHyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def get_extra_url_kwargs(self, obj):
        return {
            key: operator.attrgetter(path)(obj)
                for key, path in self.extra_url_kwargs.items()
        }

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        lookup_field = getattr(obj, self.lookup_field, None)
        kwargs = {self.lookup_field: lookup_field}
        kwargs.update(self.get_extra_url_kwargs(obj))
        # Handle unsaved object case
        if lookup_field is None:
            return None

        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except NoReverseMatch:
            pass

        if self.pk_url_kwarg != 'pk':
            # Only try pk lookup if it has been explicitly set.
            # Otherwise, the default `lookup_field = 'pk'` has us covered.
            kwargs = {self.pk_url_kwarg: obj.pk}
            kwargs.update(self.get_extra_url_kwargs(obj))
            try:
                return reverse(view_name, kwargs=kwargs, request=request, format=format)
            except NoReverseMatch:
                pass

        slug = getattr(obj, self.slug_field, None)
        if slug:
            # Only use slug lookup if a slug field exists on the model
            kwargs = {self.slug_url_kwarg: slug}
            kwargs.update(self.get_extra_url_kwargs(obj))
            try:
                return reverse(view_name, kwargs=kwargs, request=request, format=format)
            except NoReverseMatch:
                pass

        raise NoReverseMatch()


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
            "no_such_option":_("Option {value} does not exist."),
            "invalid": _('Wrong type, {error}.'),
        }
        super(AttributeValueField, self).__init__(**kwargs)

    def get_value(self, data):
        # return all the data because this field uses everything
        return data

    @wrap_in_dict("value")
    def to_internal_value(self, data):
        product_id, code, value = attribute_details(data)

        internal_value = value
        try:
            # we need the attribute to determine the type of the value
            attribute = ProductAttribute.objects.get(
                code=code,
                product_class__products__id=product_id
            )
            if attribute.required and value is None:
                self.fail('required')

            # some of these attribute types need special processing, or their
            # validation will fail
            if attribute.type == attribute.OPTION:
                internal_value = attribute.option_group.options.get(option=value)
            elif attribute.type == attribute.MULTI_OPTION:
                if attribute.required and not value:
                    self.fail('required')
                internal_value = attribute.option_group.options.filter(option__in=value)
                if len(value) != internal_value.count():
                    non_existing = set(value) - set(internal_value.values_list("option", flat=True))
                    non_existing_as_error = ",".join(sorted(non_existing))
                    self.fail('no_such_option', value=non_existing_as_error)
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

        except ProductAttribute.DoesNotExist:  # maybe this is fatal I don;t know yet
            logger.error(
                "No attribute found %s, returning value without parsing" % data)
        except ObjectDoesNotExist as e:
            self.fail("no_such_option", value=value)

        return internal_value

    def to_representation(self, obj):
        obj_type = obj.attribute.type
        if obj_type == obj.attribute.OPTION:
            return obj.value.option
        elif obj_type == obj.attribute.MULTI_OPTION:
            return obj.value.values_list('option', flat=True)
        elif obj_type == obj.attribute.FILE:
            return obj.value.url
        elif obj_type == obj.attribute.IMAGE:
            return obj.value.url
        elif obj_type == obj.attribute.ENTITY:
            if hasattr(obj.value, 'json'):
                return obj.value.json()
            else:
                return _(
                    "%(entity)s has no json method, can not convert to json" % {
                        'entity': repr(obj.value)
                    }
                )

        # return the value as stored on ProductAttributeValue in the correct type
        return obj.value
