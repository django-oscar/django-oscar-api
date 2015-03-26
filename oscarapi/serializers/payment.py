from __future__ import unicode_literals

from oscar.core.loading import get_model

from oscarapi.utils import (
    OscarHyperlinkedModelSerializer,
)

SourceType = get_model('payment', 'SourceType')


class SourceTypeSerializer(OscarHyperlinkedModelSerializer):

    class Meta:
        model = SourceType