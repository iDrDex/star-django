# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0025_cleanup_series_annotation'),
    ]

    operations = [
        migrations.RenameModel('SerieAnnotation', 'SeriesAnnotation'),
        migrations.RenameField('SampleAnnotation', 'serie_annotation', 'series_annotation'),
        migrations.RunSQL(
            """update core_statisticcache set slug = 'series_annotations'
               where slug = 'serie_annotations'""",
            """update core_statisticcache set slug = 'serie_annotations'
               where slug = 'series_annotations'""",
        ),
        migrations.RunSQL(
            """update core_statisticcache set slug = 'series_annotations'
               where slug = 'serie_annotations'""",
            """update core_statisticcache set slug = 'serie_annotations'
               where slug = 'series_annotations'""",
        ),
        migrations.AlterField(
            model_name='seriestag',
            name='created_by',
            field=models.ForeignKey(related_name='+', db_column=b'created_by', blank=True, to='core.User', null=True),
        ),
    ]
