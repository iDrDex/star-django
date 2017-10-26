# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0027_use_gin_on_series'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='platformprobe',
            name='id',
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[migrations.AlterField(
                model_name='platformprobe',
                name='platform',
                field=models.ForeignKey(related_name='probes', primary_key=True, serialize=False, to='legacy.Platform'),
            )]
        )
    ]
