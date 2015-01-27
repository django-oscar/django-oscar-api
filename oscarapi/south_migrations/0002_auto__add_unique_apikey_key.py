# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding unique constraint on 'ApiKey', fields ['key']
        db.create_unique(u'oscarapi_apikey', ['key'])


    def backwards(self, orm):
        # Removing unique constraint on 'ApiKey', fields ['key']
        db.delete_unique(u'oscarapi_apikey', ['key'])


    models = {
        u'oscarapi.apikey': {
            'Meta': {'object_name': 'ApiKey'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['oscarapi']