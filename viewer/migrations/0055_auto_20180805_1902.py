# Generated by Django 2.1 on 2018-08-05 23:02

from django.db import migrations, models
import viewer.models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0054_auto_20171212_2053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='archive',
            name='thumbnail',
            field=models.ImageField(blank=True, default='', height_field='thumbnail_height', max_length=500, upload_to=viewer.models.thumb_path_handler, width_field='thumbnail_width'),
        ),
        migrations.AlterField(
            model_name='wantedgallery',
            name='add_as_hidden',
            field=models.BooleanField(blank=True, default=False, verbose_name='Add as hidden'),
        ),
        migrations.AlterField(
            model_name='wantedgallery',
            name='found',
            field=models.BooleanField(blank=True, default=False, verbose_name='Found'),
        ),
        migrations.AlterField(
            model_name='wantedgallery',
            name='keep_searching',
            field=models.BooleanField(blank=True, default=False, verbose_name='Keep searching'),
        ),
        migrations.AlterField(
            model_name='wantedgallery',
            name='should_search',
            field=models.BooleanField(blank=True, default=False, verbose_name='Should search'),
        ),
        migrations.AlterField(
            model_name='wantedgallery',
            name='wanted_tags_exclusive_scope',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
