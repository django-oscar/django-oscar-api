from rest_framework import serializers
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
