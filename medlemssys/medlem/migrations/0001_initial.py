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
        # Adding model 'Val'
        db.create_table('medlem_val', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tittel', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('forklaring', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('medlem', ['Val'])

        # Adding model 'Lokallag'
        db.create_table('medlem_lokallag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('namn', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=255, blank=True)),
            ('fylkeslag', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('distrikt', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('andsvar', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('lokalsats', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('aktivt', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('medlem', ['Lokallag'])

        # Adding model 'Innmeldingstype'
        db.create_table('medlem_innmeldingstype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('namn', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('medlem', ['Innmeldingstype'])

        # Adding model 'Nemnd'
        db.create_table('medlem_nemnd', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('namn', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('start', self.gf('django.db.models.fields.DateField')(default=datetime.date.today)),
            ('stopp', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('medlem', ['Nemnd'])

        # Adding model 'Tilskiping'
        db.create_table('medlem_tilskiping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('namn', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=64)),
            ('start', self.gf('django.db.models.fields.DateField')(default=datetime.date.today)),
            ('stopp', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('medlem', ['Tilskiping'])

        # Adding model 'Medlem'
        db.create_table('medlem_medlem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fornamn', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('mellomnamn', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('etternamn', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('fodt', self.gf('django.db.models.fields.IntegerField')(max_length=4, null=True, blank=True)),
            ('postnr', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('epost', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('postadr', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ekstraadr', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('mobnr', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('heimenr', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('bortepostnr', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('borteadr', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('gjer', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('kjon', self.gf('django.db.models.fields.CharField')(default='U', max_length=1)),
            ('merknad', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('_siste_medlemspengar', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True, blank=True)),
            ('innmeldt_dato', self.gf('django.db.models.fields.DateField')(default=datetime.date.today)),
            ('utmeldt_dato', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='M', max_length=1)),
            ('innmeldingstype', self.gf('django.db.models.fields.CharField')(default='U', max_length=1)),
            ('innmeldingsdetalj', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('verva_av', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='har_verva', null=True, to=orm['medlem.Medlem'])),
            ('betalt_av', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='betalar_for', null=True, to=orm['medlem.Medlem'])),
            ('lokallag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['medlem.Lokallag'], null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, null=True, blank=True)),
            ('oppretta', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('oppdatert', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('medlem', ['Medlem'])

        # Adding M2M table for field val on 'Medlem'
        db.create_table('medlem_medlem_val', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('medlem', models.ForeignKey(orm['medlem.medlem'], null=False)),
            ('val', models.ForeignKey(orm['medlem.val'], null=False))
        ))
        db.create_unique('medlem_medlem_val', ['medlem_id', 'val_id'])

        # Adding M2M table for field nemnd on 'Medlem'
        db.create_table('medlem_medlem_nemnd', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('medlem', models.ForeignKey(orm['medlem.medlem'], null=False)),
            ('nemnd', models.ForeignKey(orm['medlem.nemnd'], null=False))
        ))
        db.create_unique('medlem_medlem_nemnd', ['medlem_id', 'nemnd_id'])

        # Adding M2M table for field tilskiping on 'Medlem'
        db.create_table('medlem_medlem_tilskiping', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('medlem', models.ForeignKey(orm['medlem.medlem'], null=False)),
            ('tilskiping', models.ForeignKey(orm['medlem.tilskiping'], null=False))
        ))
        db.create_unique('medlem_medlem_tilskiping', ['medlem_id', 'tilskiping_id'])

        # Adding model 'Giro'
        db.create_table('medlem_giro', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('medlem', self.gf('django.db.models.fields.related.ForeignKey')(related_name='giroar', to=orm['medlem.Medlem'])),
            ('belop', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('innbetalt_belop', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('kid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, blank=True)),
            ('oppretta', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('oppdatert', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('innbetalt', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('konto', self.gf('django.db.models.fields.CharField')(default='M', max_length=1)),
            ('hensikt', self.gf('django.db.models.fields.CharField')(default='P', max_length=1)),
            ('desc', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='V', max_length=1)),
            ('gjeldande_aar', self.gf('django.db.models.fields.PositiveIntegerField')(default=2013)),
        ))
        db.send_create_signal('medlem', ['Giro'])

        # Adding model 'Rolletype'
        db.create_table('medlem_rolletype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('namn', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('medlem', ['Rolletype'])

        # Adding model 'Rolle'
        db.create_table('medlem_rolle', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('medlem', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['medlem.Medlem'])),
            ('lokallag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['medlem.Lokallag'])),
            ('rolletype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['medlem.Rolletype'], null=True, blank=True)),
        ))
        db.send_create_signal('medlem', ['Rolle'])

        # Adding model 'LokallagOvervaking'
        db.create_table('medlem_lokallagovervaking', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('medlem', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['medlem.Medlem'], null=True, blank=True)),
            ('epost', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('lokallag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['medlem.Lokallag'])),
            ('deaktivert', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('sist_oppdatert', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('medlem', ['LokallagOvervaking'])

        # Adding model 'PostNummer'
        db.create_table('medlem_postnummer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('postnr', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('poststad', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('bruksomrade', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('folketal', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('bydel', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('kommnr', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('kommune', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('fylke', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('lat', self.gf('django.db.models.fields.FloatField')()),
            ('lon', self.gf('django.db.models.fields.FloatField')()),
            ('datakvalitet', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('sist_oppdatert', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('medlem', ['PostNummer'])


    def backwards(self, orm):
        # Deleting model 'Val'
        db.delete_table('medlem_val')

        # Deleting model 'Lokallag'
        db.delete_table('medlem_lokallag')

        # Deleting model 'Innmeldingstype'
        db.delete_table('medlem_innmeldingstype')

        # Deleting model 'Nemnd'
        db.delete_table('medlem_nemnd')

        # Deleting model 'Tilskiping'
        db.delete_table('medlem_tilskiping')

        # Deleting model 'Medlem'
        db.delete_table('medlem_medlem')

        # Removing M2M table for field val on 'Medlem'
        db.delete_table('medlem_medlem_val')

        # Removing M2M table for field nemnd on 'Medlem'
        db.delete_table('medlem_medlem_nemnd')

        # Removing M2M table for field tilskiping on 'Medlem'
        db.delete_table('medlem_medlem_tilskiping')

        # Deleting model 'Giro'
        db.delete_table('medlem_giro')

        # Deleting model 'Rolletype'
        db.delete_table('medlem_rolletype')

        # Deleting model 'Rolle'
        db.delete_table('medlem_rolle')

        # Deleting model 'LokallagOvervaking'
        db.delete_table('medlem_lokallagovervaking')

        # Deleting model 'PostNummer'
        db.delete_table('medlem_postnummer')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'medlem.giro': {
            'Meta': {'ordering': "('-oppdatert', '-innbetalt', '-pk')", 'object_name': 'Giro'},
            'belop': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'desc': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'gjeldande_aar': ('django.db.models.fields.PositiveIntegerField', [], {'default': '2013'}),
            'hensikt': ('django.db.models.fields.CharField', [], {'default': "'P'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'innbetalt': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'innbetalt_belop': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'kid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'konto': ('django.db.models.fields.CharField', [], {'default': "'M'", 'max_length': '1'}),
            'medlem': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'giroar'", 'to': "orm['medlem.Medlem']"}),
            'oppdatert': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'oppretta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'V'", 'max_length': '1'})
        },
        'medlem.innmeldingstype': {
            'Meta': {'object_name': 'Innmeldingstype'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'namn': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
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
        'medlem.lokallagovervaking': {
            'Meta': {'object_name': 'LokallagOvervaking'},
            'deaktivert': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'epost': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lokallag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['medlem.Lokallag']"}),
            'medlem': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['medlem.Medlem']", 'null': 'True', 'blank': 'True'}),
            'sist_oppdatert': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'medlem.medlem': {
            'Meta': {'ordering': "['-id']", 'object_name': 'Medlem'},
            '_siste_medlemspengar': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'betalt_av': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'betalar_for'", 'null': 'True', 'to': "orm['medlem.Medlem']"}),
            'borteadr': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'bortepostnr': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'ekstraadr': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'epost': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'etternamn': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'fodt': ('django.db.models.fields.IntegerField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fornamn': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'gjer': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'heimenr': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'innmeldingsdetalj': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'innmeldingstype': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'innmeldt_dato': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'kjon': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'lokallag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['medlem.Lokallag']", 'null': 'True', 'blank': 'True'}),
            'lokallagsrolle': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'rollemedlem'", 'to': "orm['medlem.Lokallag']", 'through': "orm['medlem.Rolle']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'mellomnamn': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'merknad': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'mobnr': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'nemnd': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['medlem.Nemnd']", 'null': 'True', 'blank': 'True'}),
            'oppdatert': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'oppretta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'postadr': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'postnr': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'M'", 'max_length': '1'}),
            'tilskiping': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['medlem.Tilskiping']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'utmeldt_dato': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['medlem.Val']", 'null': 'True', 'blank': 'True'}),
            'verva_av': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'har_verva'", 'null': 'True', 'to': "orm['medlem.Medlem']"})
        },
        'medlem.nemnd': {
            'Meta': {'object_name': 'Nemnd'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'namn': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'start': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'stopp': ('django.db.models.fields.DateField', [], {})
        },
        'medlem.postnummer': {
            'Meta': {'object_name': 'PostNummer'},
            'bruksomrade': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'bydel': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'datakvalitet': ('django.db.models.fields.SmallIntegerField', [], {}),
            'folketal': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fylke': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kommnr': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'kommune': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'lat': ('django.db.models.fields.FloatField', [], {}),
            'lon': ('django.db.models.fields.FloatField', [], {}),
            'postnr': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'poststad': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'sist_oppdatert': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'medlem.rolle': {
            'Meta': {'ordering': "['rolletype', 'medlem']", 'object_name': 'Rolle'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lokallag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['medlem.Lokallag']"}),
            'medlem': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['medlem.Medlem']"}),
            'rolletype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['medlem.Rolletype']", 'null': 'True', 'blank': 'True'})
        },
        'medlem.rolletype': {
            'Meta': {'ordering': "['namn']", 'object_name': 'Rolletype'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'namn': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'medlem.tilskiping': {
            'Meta': {'object_name': 'Tilskiping'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'namn': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '64'}),
            'start': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'stopp': ('django.db.models.fields.DateField', [], {})
        },
        'medlem.val': {
            'Meta': {'object_name': 'Val'},
            'forklaring': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tittel': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['medlem']
