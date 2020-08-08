# Generated by Django 3.0.7 on 2020-08-05 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0090_artist_twitter_handle'),
    ]

    operations = [
        migrations.AddField(
            model_name='wantedgallery',
            name='regexp_search_title',
            field=models.BooleanField(blank=True, default=False, verbose_name='Regexp search title'),
        ),
        migrations.AddField(
            model_name='wantedgallery',
            name='regexp_unwanted_title',
            field=models.BooleanField(blank=True, default=False, verbose_name='Regexp unwanted title'),
        ),
    ]
