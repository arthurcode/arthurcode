# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Discount.amount_type'
        db.delete_column('coupons_discount', 'amount_type')

        # Adding field 'Discount.type'
        db.add_column('coupons_discount', 'type',
                      self.gf('django.db.models.fields.SmallIntegerField')(default=1),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Discount.amount_type'
        db.add_column('coupons_discount', 'amount_type',
                      self.gf('django.db.models.fields.SmallIntegerField')(default=1),
                      keep_default=False)

        # Deleting field 'Discount.type'
        db.delete_column('coupons_discount', 'type')


    models = {
        'coupons.discount': {
            'Meta': {'object_name': 'Discount'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'applies_to': ('django.db.models.fields.SmallIntegerField', [], {}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'redemption_scheme': ('django.db.models.fields.SmallIntegerField', [], {}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        }
    }

    complete_apps = ['coupons']