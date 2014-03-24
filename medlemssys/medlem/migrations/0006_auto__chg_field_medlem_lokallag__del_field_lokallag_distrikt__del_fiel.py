# -*- coding: utf-8 -*-

# Copyright 2009-2014 Odin Hørthe Omdal

# This file is part of Medlemssys.

# Medlemssys is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Medlemssys is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Medlemssys.  If not, see <http://www.gnu.org/licenses/>.
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Medlem.lokallag'
        db.alter_column(u'medlem_medlem', 'lokallag_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['medlem.Lokallag'], null=True, on_delete=models.SET_NULL))
        # Deleting field 'Lokallag.distrikt'
        db.delete_column(u'medlem_lokallag', 'distrikt')

        # Deleting field 'Lokallag.fylkeslag'
        db.delete_column(u'medlem_lokallag', 'fylkeslag')

        # Adding field 'Lokallag.kommunes'
        db.add_column(u'medlem_lokallag', 'kommunes',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        # Adding field 'Lokallag.fylke'
        db.add_column(u'medlem_lokallag', 'fylke',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)


    def backwards(self, orm):

        # Changing field 'Medlem.lokallag'
        db.alter_column(u'medlem_medlem', 'lokallag_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['medlem.Lokallag'], null=True))
        # Adding field 'Lokallag.distrikt'
        db.add_column(u'medlem_lokallag', 'distrikt',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        # Adding field 'Lokallag.fylkeslag'
        db.add_column(u'medlem_lokallag', 'fylkeslag',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        # Deleting field 'Lokallag.kommunes'
        db.delete_column(u'medlem_lokallag', 'kommunes')

        # Deleting field 'Lokallag.fylke'
        db.delete_column(u'medlem_lokallag', 'fylke')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'medlem.giro': {
            'Meta': {'ordering': "('-oppdatert', '-innbetalt', '-pk')", 'object_name': 'Giro'},
            'belop': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'desc': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'gjeldande_aar': ('django.db.models.fields.PositiveIntegerField', [], {'default': '2013'}),
            'hensikt': ('django.db.models.fields.CharField', [], {'default': "'P'", 'max_length': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'innbetalt': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'innbetalt_belop': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'kid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'konto': ('django.db.models.fields.CharField', [], {'default': "'M'", 'max_length': '1'}),
            'medlem': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'giroar'", 'to': u"orm['medlem.Medlem']"}),
            'oppdatert': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'oppretta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'V'", 'max_length': '1'})
        },
        u'medlem.innmeldingstype': {
            'Meta': {'object_name': 'Innmeldingstype'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'namn': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'medlem.lokallag': {
            'Meta': {'ordering': "['-aktivt', 'namn']", 'object_name': 'Lokallag'},
            'aktivt': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'andsvar': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'epost': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'fylke': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kommunes': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'lokalsats': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'namn': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'})
        },
        u'medlem.lokallagovervaking': {
            'Meta': {'object_name': 'LokallagOvervaking'},
            'deaktivert': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'epost': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lokallag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['medlem.Lokallag']"}),
            'medlem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['medlem.Medlem']", 'null': 'True', 'blank': 'True'}),
            'sist_oppdatert': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'medlem.medlem': {
            'Meta': {'ordering': "['-id']", 'object_name': 'Medlem'},
            '_siste_medlemspengar': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'betalt_av': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'betalar_for'", 'null': 'True', 'to': u"orm['medlem.Medlem']"}),
            'borteadr': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'bortepostnr': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ekstraadr': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'epost': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'etternamn': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'fodt': ('django.db.models.fields.IntegerField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fornamn': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'gjer': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'heimenr': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'innmeldingsdetalj': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'innmeldingstype': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'innmeldt_dato': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'kjon': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'lokallag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['medlem.Lokallag']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'lokallagsrolle': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'rollemedlem'", 'to': u"orm['medlem.Lokallag']", 'through': u"orm['medlem.Rolle']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'mellomnamn': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'merknad': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'mobnr': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'nykel': ('django.db.models.fields.CharField', [], {'default': "'ymtpcdt'", 'max_length': '255', 'blank': 'True'}),
            'oppdatert': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'oppretta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'postadr': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'postnr': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'M'", 'max_length': '1'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'utmeldt_dato': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['medlem.Val']", 'null': 'True', 'blank': 'True'}),
            'verva_av': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'har_verva'", 'null': 'True', 'to': u"orm['medlem.Medlem']"})
        },
        u'medlem.postnummer': {
            'Meta': {'object_name': 'PostNummer'},
            'bruksomrade': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'bydel': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'datakvalitet': ('django.db.models.fields.SmallIntegerField', [], {}),
            'folketal': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fylke': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kommnr': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'kommune': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'lat': ('django.db.models.fields.FloatField', [], {}),
            'lon': ('django.db.models.fields.FloatField', [], {}),
            'postnr': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'poststad': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'sist_oppdatert': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'medlem.rolle': {
            'Meta': {'ordering': "['rolletype', 'medlem']", 'object_name': 'Rolle'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lokallag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['medlem.Lokallag']"}),
            'medlem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['medlem.Medlem']"}),
            'rolletype': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['medlem.Rolletype']", 'null': 'True', 'blank': 'True'})
        },
        u'medlem.rolletype': {
            'Meta': {'ordering': "['namn']", 'object_name': 'Rolletype'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'namn': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'medlem.val': {
            'Meta': {'object_name': 'Val'},
            'forklaring': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tittel': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['medlem']
