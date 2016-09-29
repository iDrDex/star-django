# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0013_silent_blank_change'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sampleattribute',
            name='sample',
        ),
        migrations.RemoveField(
            model_name='seriesattribute',
            name='series',
        ),
        migrations.DeleteModel(
            name='SampleAttribute',
        ),
        migrations.DeleteModel(
            name='SeriesAttribute',
        ),
        migrations.RunSQL("""
            drop materialized view series_tag_view;
            drop materialized view sample_tag_view;
        """)
    ]
