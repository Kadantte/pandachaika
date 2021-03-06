# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-16 20:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0020_wantedgallery_add_as_hidden'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='archivematches',
            options={'ordering': ['-match_accuracy'], 'verbose_name_plural': 'Archive matches'},
        ),
        migrations.AddField(
            model_name='archive',
            name='extracted',
            field=models.BooleanField(default=False),
        ),
    ]
