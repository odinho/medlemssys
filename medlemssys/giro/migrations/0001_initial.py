# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GiroTemplate'
        db.create_table('giro_girotemplate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('text_template', self.gf('django.db.models.fields.TextField')()),
            ('html_template', self.gf('django.db.models.fields.TextField')()),
            ('trigger', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
        ))
        db.send_create_signal('giro', ['GiroTemplate'])


    def backwards(self, orm):
        # Deleting model 'GiroTemplate'
        db.delete_table('giro_girotemplate')


    models = {
        'giro.girotemplate': {
            'Meta': {'object_name': 'GiroTemplate'},
            'html_template': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'text_template': ('django.db.models.fields.TextField', [], {}),
            'trigger': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['giro']