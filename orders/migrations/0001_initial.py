# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Order'
        db.create_table('orders_order', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=50, null=True, blank=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('contact_method', self.gf('django.db.models.fields.SmallIntegerField')(default=2)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(default=1)),
            ('ip_address', self.gf('django.db.models.fields.IPAddressField')(default='0.0.0.0', max_length=15)),
            ('is_pickup', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('shipping_charge', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
        ))
        db.send_create_signal('orders', ['Order'])

        # Adding model 'OrderItem'
        db.create_table('orders_orderitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['orders.Order'])),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.ProductInstance'])),
            ('quantity', self.gf('django.db.models.fields.IntegerField')()),
            ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
        ))
        db.send_create_signal('orders', ['OrderItem'])

        # Adding model 'OrderBillingAddress'
        db.create_table('orders_orderbillingaddress', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('line1', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('line2', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('country', self.gf('django_countries.fields.CountryField')(max_length=2)),
            ('post_code', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.related.OneToOneField')(related_name='billing_address', unique=True, to=orm['orders.Order'])),
        ))
        db.send_create_signal('orders', ['OrderBillingAddress'])

        # Adding model 'OrderShippingAddress'
        db.create_table('orders_ordershippingaddress', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('line1', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('line2', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('country', self.gf('django_countries.fields.CountryField')(max_length=2)),
            ('post_code', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.related.OneToOneField')(related_name='shipping_address', unique=True, to=orm['orders.Order'])),
        ))
        db.send_create_signal('orders', ['OrderShippingAddress'])

        # Adding model 'OrderTax'
        db.create_table('orders_ordertax', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(related_name='taxes', to=orm['orders.Order'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('rate', self.gf('django.db.models.fields.DecimalField')(max_digits=7, decimal_places=4)),
            ('total', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
        ))
        db.send_create_signal('orders', ['OrderTax'])

        # Adding model 'CreditCardPayment'
        db.create_table('orders_creditcardpayment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
            ('order', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['orders.Order'], unique=True)),
            ('transaction_id', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('token', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('status', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('card_type', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal('orders', ['CreditCardPayment'])


    def backwards(self, orm):
        # Deleting model 'Order'
        db.delete_table('orders_order')

        # Deleting model 'OrderItem'
        db.delete_table('orders_orderitem')

        # Deleting model 'OrderBillingAddress'
        db.delete_table('orders_orderbillingaddress')

        # Deleting model 'OrderShippingAddress'
        db.delete_table('orders_ordershippingaddress')

        # Deleting model 'OrderTax'
        db.delete_table('orders_ordertax')

        # Deleting model 'CreditCardPayment'
        db.delete_table('orders_creditcardpayment')


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
        'catalogue.product': {
            'Meta': {'object_name': 'Product'},
            'awards': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'products'", 'blank': 'True', 'to': "orm['catalogue.AwardInstance']"}),
            'brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': "orm['catalogue.Brand']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Category']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bestseller': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_box_stuffer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_green': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'long_description': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'sale_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2', 'blank': 'True'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'}),
            'themes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'products'", 'blank': 'True', 'to': "orm['catalogue.Theme']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
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
        'catalogue.theme': {
            'Meta': {'object_name': 'Theme'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'orders.creditcardpayment': {
            'Meta': {'object_name': 'CreditCardPayment'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'card_type': ('django.db.models.fields.SmallIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['orders.Order']", 'unique': 'True'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'transaction_id': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'orders.order': {
            'Meta': {'object_name': 'Order'},
            'contact_method': ('django.db.models.fields.SmallIntegerField', [], {'default': '2'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'default': "'0.0.0.0'", 'max_length': '15'}),
            'is_pickup': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'shipping_charge': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'orders.orderbillingaddress': {
            'Meta': {'object_name': 'OrderBillingAddress'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'country': ('django_countries.fields.CountryField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line1': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'line2': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'billing_address'", 'unique': 'True', 'to': "orm['orders.Order']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'post_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'orders.orderitem': {
            'Meta': {'object_name': 'OrderItem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.ProductInstance']"}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['orders.Order']"}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {})
        },
        'orders.ordershippingaddress': {
            'Meta': {'object_name': 'OrderShippingAddress'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'country': ('django_countries.fields.CountryField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line1': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'line2': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'shipping_address'", 'unique': 'True', 'to': "orm['orders.Order']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'post_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'orders.ordertax': {
            'Meta': {'object_name': 'OrderTax'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taxes'", 'to': "orm['orders.Order']"}),
            'rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '7', 'decimal_places': '4'}),
            'total': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'})
        }
    }

    complete_apps = ['orders']