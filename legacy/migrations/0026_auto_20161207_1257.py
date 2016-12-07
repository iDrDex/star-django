# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0025_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='series',
            name='platforms',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=127), size=None),
        ),
    ]
