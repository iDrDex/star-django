# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_create_users_tokens'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryStatisticCache',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('series_count', models.PositiveIntegerField()),
                ('samples_count', models.PositiveIntegerField()),
                ('platforms_count', models.PositiveIntegerField()),
                ('probes_count', models.PositiveIntegerField()),
                ('users_count', models.PositiveIntegerField()),
                ('tags_count', models.PositiveIntegerField()),
                ('annotations_count', models.PositiveIntegerField()),
            ],
        ),
    ]
