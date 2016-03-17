# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Category'
        db.create_table('captcha_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('max_number', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('captcha', ['Category'])


    def backwards(self, orm):
        # Deleting model 'Category'
        db.delete_table('captcha_category')


    models = {
        'captcha.captcha': {
            'Meta': {'object_name': 'Captcha'},
            'add_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_hash': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'label_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'captcha.category': {
            'Meta': {'object_name': 'Category'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_number': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        'captcha.labellog': {
            'Meta': {'object_name': 'LabelLog'},
            'add_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'captcha': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['captcha.Captcha']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['captcha']