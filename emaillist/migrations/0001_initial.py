# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EmailListItem'
        db.create_table('emaillist_emaillistitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
            ('date_added', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
        ))
        db.send_create_signal('emaillist', ['EmailListItem'])


    def backwards(self, orm):
        # Deleting model 'EmailListItem'
        db.delete_table('emaillist_emaillistitem')


    models = {
        'emaillist.emaillistitem': {
            'Meta': {'object_name': 'EmailListItem'},
            'date_added': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['emaillist']