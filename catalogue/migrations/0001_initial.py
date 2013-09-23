# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Category'
        db.create_table('catalogue_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(blank=True, related_name='children', null=True, to=orm['catalogue.Category'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('catalogue', ['Category'])

        # Adding model 'Award'
        db.create_table('catalogue_award', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('short_description', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('long_description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('catalogue', ['Award'])

        # Adding model 'AwardInstance'
        db.create_table('catalogue_awardinstance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('award', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.Award'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('catalogue', ['AwardInstance'])

        # Adding model 'Brand'
        db.create_table('catalogue_brand', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('short_description', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('long_description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('catalogue', ['Brand'])

        # Adding model 'Theme'
        db.create_table('catalogue_theme', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('short_description', self.gf('django.db.models.fields.CharField')(max_length=500)),
        ))
        db.send_create_signal('catalogue', ['Theme'])

        # Adding model 'Product'
        db.create_table('catalogue_product', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=255)),
            ('brand', self.gf('django.db.models.fields.related.ForeignKey')(related_name='products', to=orm['catalogue.Brand'])),
            ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
            ('sale_price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2, blank=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_bestseller', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_featured', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_box_stuffer', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_green', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('meta_description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('short_description', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('long_description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.Category'])),
            ('min_age', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('max_age', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('weight', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=3)),
            ('length', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=2, blank=True)),
            ('width', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=2, blank=True)),
            ('height', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('catalogue', ['Product'])

        # Adding M2M table for field awards on 'Product'
        db.create_table('catalogue_product_awards', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('product', models.ForeignKey(orm['catalogue.product'], null=False)),
            ('awardinstance', models.ForeignKey(orm['catalogue.awardinstance'], null=False))
        ))
        db.create_unique('catalogue_product_awards', ['product_id', 'awardinstance_id'])

        # Adding M2M table for field themes on 'Product'
        db.create_table('catalogue_product_themes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('product', models.ForeignKey(orm['catalogue.product'], null=False)),
            ('theme', models.ForeignKey(orm['catalogue.theme'], null=False))
        ))
        db.create_unique('catalogue_product_themes', ['product_id', 'theme_id'])

        # Adding model 'Specification'
        db.create_table('catalogue_specification', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='specifications', to=orm['catalogue.Product'])),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=75)),
        ))
        db.send_create_signal('catalogue', ['Specification'])

        # Adding model 'ProductOption'
        db.create_table('catalogue_productoption', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('category', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('catalogue', ['ProductOption'])

        # Adding unique constraint on 'ProductOption', fields ['category', 'name']
        db.create_unique('catalogue_productoption', ['category', 'name'])

        # Adding model 'Color'
        db.create_table('catalogue_color', (
            ('productoption_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['catalogue.ProductOption'], unique=True, primary_key=True)),
            ('html', self.gf('django.db.models.fields.CharField')(max_length=25)),
        ))
        db.send_create_signal('catalogue', ['Color'])

        # Adding model 'Size'
        db.create_table('catalogue_size', (
            ('productoption_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['catalogue.ProductOption'], unique=True, primary_key=True)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('sort_index', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('catalogue', ['Size'])

        # Adding model 'ProductInstance'
        db.create_table('catalogue_productinstance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='instances', to=orm['catalogue.Product'])),
            ('quantity', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('sku', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10)),
        ))
        db.send_create_signal('catalogue', ['ProductInstance'])

        # Adding M2M table for field options on 'ProductInstance'
        db.create_table('catalogue_productinstance_options', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('productinstance', models.ForeignKey(orm['catalogue.productinstance'], null=False)),
            ('productoption', models.ForeignKey(orm['catalogue.productoption'], null=False))
        ))
        db.create_unique('catalogue_productinstance_options', ['productinstance_id', 'productoption_id'])

        # Adding model 'ProductImage'
        db.create_table('catalogue_productimage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='images', to=orm['catalogue.Product'])),
            ('is_primary', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('detail_path', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('thumb_path', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('alt_text', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('option', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.ProductOption'], null=True, blank=True)),
        ))
        db.send_create_signal('catalogue', ['ProductImage'])

        # Adding model 'RestockNotification'
        db.create_table('catalogue_restocknotification', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('instance', self.gf('django.db.models.fields.related.ForeignKey')(related_name='restock_notifications', to=orm['catalogue.ProductInstance'])),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
        ))
        db.send_create_signal('catalogue', ['RestockNotification'])

        # Adding unique constraint on 'RestockNotification', fields ['instance', 'email']
        db.create_unique('catalogue_restocknotification', ['instance_id', 'email'])


    def backwards(self, orm):
        # Removing unique constraint on 'RestockNotification', fields ['instance', 'email']
        db.delete_unique('catalogue_restocknotification', ['instance_id', 'email'])

        # Removing unique constraint on 'ProductOption', fields ['category', 'name']
        db.delete_unique('catalogue_productoption', ['category', 'name'])

        # Deleting model 'Category'
        db.delete_table('catalogue_category')

        # Deleting model 'Award'
        db.delete_table('catalogue_award')

        # Deleting model 'AwardInstance'
        db.delete_table('catalogue_awardinstance')

        # Deleting model 'Brand'
        db.delete_table('catalogue_brand')

        # Deleting model 'Theme'
        db.delete_table('catalogue_theme')

        # Deleting model 'Product'
        db.delete_table('catalogue_product')

        # Removing M2M table for field awards on 'Product'
        db.delete_table('catalogue_product_awards')

        # Removing M2M table for field themes on 'Product'
        db.delete_table('catalogue_product_themes')

        # Deleting model 'Specification'
        db.delete_table('catalogue_specification')

        # Deleting model 'ProductOption'
        db.delete_table('catalogue_productoption')

        # Deleting model 'Color'
        db.delete_table('catalogue_color')

        # Deleting model 'Size'
        db.delete_table('catalogue_size')

        # Deleting model 'ProductInstance'
        db.delete_table('catalogue_productinstance')

        # Removing M2M table for field options on 'ProductInstance'
        db.delete_table('catalogue_productinstance_options')

        # Deleting model 'ProductImage'
        db.delete_table('catalogue_productimage')

        # Deleting model 'RestockNotification'
        db.delete_table('catalogue_restocknotification')


    models = {
        'catalogue.award': {
            'Meta': {'object_name': 'Award'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_description': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'catalogue.awardinstance': {
            'Meta': {'object_name': 'AwardInstance'},
            'award': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Award']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'catalogue.brand': {
            'Meta': {'object_name': 'Brand'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_description': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'catalogue.category': {
            'Meta': {'ordering': "['tree_id', 'lft']", 'object_name': 'Category'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['catalogue.Category']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'catalogue.color': {
            'Meta': {'object_name': 'Color', '_ormbases': ['catalogue.ProductOption']},
            'html': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'productoption_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['catalogue.ProductOption']", 'unique': 'True', 'primary_key': 'True'})
        },
        'catalogue.product': {
            'Meta': {'object_name': 'Product'},
            'awards': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'products'", 'blank': 'True', 'to': "orm['catalogue.AwardInstance']"}),
            'brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': "orm['catalogue.Brand']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Category']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bestseller': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_box_stuffer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_green': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'length': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'long_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'max_age': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'meta_description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'min_age': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'sale_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2', 'blank': 'True'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'}),
            'themes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'products'", 'blank': 'True', 'to': "orm['catalogue.Theme']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'weight': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'width': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'})
        },
        'catalogue.productimage': {
            'Meta': {'object_name': 'ProductImage'},
            'alt_text': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'detail_path': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_primary': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'option': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.ProductOption']", 'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images'", 'to': "orm['catalogue.Product']"}),
            'thumb_path': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'catalogue.productinstance': {
            'Meta': {'object_name': 'ProductInstance'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'options': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalogue.ProductOption']", 'symmetrical': 'False', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'instances'", 'to': "orm['catalogue.Product']"}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'sku': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'})
        },
        'catalogue.productoption': {
            'Meta': {'unique_together': "(('category', 'name'),)", 'object_name': 'ProductOption'},
            'category': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'catalogue.restocknotification': {
            'Meta': {'unique_together': "(('instance', 'email'),)", 'object_name': 'RestockNotification'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'restock_notifications'", 'to': "orm['catalogue.ProductInstance']"})
        },
        'catalogue.size': {
            'Meta': {'object_name': 'Size', '_ormbases': ['catalogue.ProductOption']},
            'productoption_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['catalogue.ProductOption']", 'unique': 'True', 'primary_key': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'sort_index': ('django.db.models.fields.IntegerField', [], {})
        },
        'catalogue.specification': {
            'Meta': {'object_name': 'Specification'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'specifications'", 'to': "orm['catalogue.Product']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '75'})
        },
        'catalogue.theme': {
            'Meta': {'object_name': 'Theme'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['catalogue']