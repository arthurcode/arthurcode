# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Discount'
        db.create_table('coupons_discount', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('start_date', self.gf('django.db.models.fields.DateField')()),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('amount_type', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('amount', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('redemption_scheme', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('applies_to', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal('coupons', ['Discount'])


    def backwards(self, orm):
        # Deleting model 'Discount'
        db.delete_table('coupons_discount')


    models = {
        'coupons.discount': {
            'Meta': {'object_name': 'Discount'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'amount_type': ('django.db.models.fields.SmallIntegerField', [], {}),
            'applies_to': ('django.db.models.fields.SmallIntegerField', [], {}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'redemption_scheme': ('django.db.models.fields.SmallIntegerField', [], {}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        }
    }

    complete_apps = ['coupons']