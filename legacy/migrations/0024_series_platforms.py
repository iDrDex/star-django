# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


def update_series(apps, schema_editor):
    Series = apps.get_model('legacy', 'series')

    total = Series.objects.count()
    index = 0

    for serie in Series.objects.iterator():
        index += 1
        if index % 100 == 0:
            print("{0}/{1}".format(index,total))
        serie.platforms = list(serie.samples.values_list('platform', flat=True).distinct())
        serie.samples_count = len(serie.attrs['sample_id'].split())
        serie.save()


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0023_series_specie'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='platforms',
            field=django.contrib.postgres.fields.ArrayField(size=None, base_field=models.IntegerField(), blank=True, null=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='series',
            name='samples_count',
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(
            update_series
        ),
    ]
