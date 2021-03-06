# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'AuthorProfile'
        db.create_table('blog_authorprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('pen_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100, blank=True)),
        ))
        db.send_create_signal('blog', ['AuthorProfile'])

        # Adding model 'TaggedPost'
        db.create_table('blog_taggedpost', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blog_taggedpost_items', to=orm['taggit.Tag'])),
            ('content_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['blog.Post'])),
        ))
        db.send_create_signal('blog', ['TaggedPost'])

        # Adding model 'Post'
        db.create_table('blog_post', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['blog.AuthorProfile'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('title_slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=200)),
            ('synopsis', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('pub_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('mod_date', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('enable_comments', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_draft', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('blog', ['Post'])


    def backwards(self, orm):
        # Deleting model 'AuthorProfile'
        db.delete_table('blog_authorprofile')

        # Deleting model 'TaggedPost'
        db.delete_table('blog_taggedpost')

        # Deleting model 'Post'
        db.delete_table('blog_post')


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
        'blog.authorprofile': {
            'Meta': {'object_name': 'AuthorProfile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pen_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'blog.post': {
            'Meta': {'object_name': 'Post'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['blog.AuthorProfile']"}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'enable_comments': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_draft': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'mod_date': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pub_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'synopsis': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title_slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'})
        },
        'blog.taggedpost': {
            'Meta': {'object_name': 'TaggedPost'},
            'content_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['blog.Post']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blog_taggedpost_items'", 'to': "orm['taggit.Tag']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['blog']