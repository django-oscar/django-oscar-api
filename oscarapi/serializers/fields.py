import operator

from django.urls import NoReverseMatch
from django.utils.translation import ugettext as _

from rest_framework import serializers, relations
from rest_framework.reverse import reverse
from rest_framework.fields import get_attribute


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
    def __init__(self, **kwargs):
        super(AttributeValueField, self).__init__(**kwargs)
        self.source = "*"

    def get_attribute(self, instance):
        return super().get_attribute(instance)

    def to_internal_value(self, obj):
        return {"value": obj}

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
