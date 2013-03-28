# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'LokallagStat'
        db.create_table('statistikk_lokallagstat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lokallag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['medlem.Lokallag'])),
            ('veke', self.gf('django.db.models.fields.CharField')(max_length=7)),
            ('n_teljande', self.gf('django.db.models.fields.IntegerField')()),
            ('n_interessante', self.gf('django.db.models.fields.IntegerField')()),
            ('n_ikkje_utmelde', self.gf('django.db.models.fields.IntegerField')()),
            ('n_totalt', self.gf('django.db.models.fields.IntegerField')()),
            ('teljande', self.gf('django.db.models.fields.TextField')()),
            ('interessante', self.gf('django.db.models.fields.TextField')()),
            ('oppretta', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('statistikk', ['LokallagStat'])

        # Adding unique constraint on 'LokallagStat', fields ['lokallag', 'veke']
        db.create_unique('statistikk_lokallagstat', ['lokallag_id', 'veke'])


    def backwards(self, orm):
        # Removing unique constraint on 'LokallagStat', fields ['lokallag', 'veke']
        db.delete_unique('statistikk_lokallagstat', ['lokallag_id', 'veke'])

        # Deleting model 'LokallagStat'
        db.delete_table('statistikk_lokallagstat')


    models = {
        'medlem.lokallag': {
            'Meta': {'ordering': "['-aktivt', 'namn']", 'object_name': 'Lokallag'},
            'aktivt': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'andsvar': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'distrikt': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'fylkeslag': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lokalsats': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'namn': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'})
        },
        'statistikk.lokallagstat': {
            'Meta': {'unique_together': "(('lokallag', 'veke'),)", 'object_name': 'LokallagStat'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interessante': ('django.db.models.fields.TextField', [], {}),
            'lokallag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['medlem.Lokallag']"}),
            'n_ikkje_utmelde': ('django.db.models.fields.IntegerField', [], {}),
            'n_interessante': ('django.db.models.fields.IntegerField', [], {}),
            'n_teljande': ('django.db.models.fields.IntegerField', [], {}),
            'n_totalt': ('django.db.models.fields.IntegerField', [], {}),
            'oppretta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'teljande': ('django.db.models.fields.TextField', [], {}),
            'veke': ('django.db.models.fields.CharField', [], {'max_length': '7'})
        }
    }

    complete_apps = ['statistikk']