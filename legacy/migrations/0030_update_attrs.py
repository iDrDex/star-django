# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields
import handy.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0029_drop_hidden_legacy'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='series',
            options={'verbose_name_plural': 'series'},
        ),
        migrations.AlterField(
            model_name='series',
            name='attrs',
            field=handy.models.fields.JSONField(default={}, blank=True),
        ),
        migrations.AlterField(
            model_name='series',
            name='platforms',
            field=django.contrib.postgres.fields.ArrayField(default=[], size=None, base_field=models.CharField(max_length=127), blank=True),
        ),
        migrations.AlterField(
            model_name='series',
            name='samples_count',
            field=models.IntegerField(default=0, blank=True),
        ),
    ]
