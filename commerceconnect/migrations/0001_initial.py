# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ApiKey'
        db.create_table(u'commerceconnect_apikey', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'commerceconnect', ['ApiKey'])


    def backwards(self, orm):
        # Deleting model 'ApiKey'
        db.delete_table(u'commerceconnect_apikey')


    models = {
        u'commerceconnect.apikey': {
            'Meta': {'object_name': 'ApiKey'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['commerceconnect']