# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-17 05:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0021_auto_20160516_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tweetpost',
            name='tweet_id',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
