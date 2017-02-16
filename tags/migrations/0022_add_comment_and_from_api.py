# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0021_ontologies'),
    ]

    operations = [
        migrations.AddField(
            model_name='seriestag',
            name='comment',
            field=models.CharField(max_length=512, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='seriestag',
            name='from_api',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='serievalidation',
            name='comment',
            field=models.CharField(max_length=512, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='serievalidation',
            name='from_api',
            field=models.BooleanField(default=False),
        ),
    ]
