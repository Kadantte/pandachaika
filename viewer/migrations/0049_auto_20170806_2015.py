# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-06 20:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0048_auto_20170806_0251'),
    ]

    operations = [
        migrations.AlterField(
            model_name='provider',
            name='description',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AlterField(
            model_name='provider',
            name='home_page',
            field=models.URLField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='provider',
            name='information',
            field=models.TextField(blank=True, default=''),
        ),
    ]