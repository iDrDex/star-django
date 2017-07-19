# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0027_refactor_annotations'),
    ]

    operations = [
        migrations.AddField(
            model_name='rawseriesannotation',
            name='agreed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='seriesannotation',
            name='series_tag',
            field=models.OneToOneField(related_name='canonical', null=True, to='tags.SeriesTag'),
        ),
        migrations.AlterField(
            model_name='validationjob',
            name='series_tag',
            field=models.ForeignKey(to='tags.SeriesTag', null=True),
        ),
    ]
