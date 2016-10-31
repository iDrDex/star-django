# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0014_remove_attr_tables_and_views'),
    ]

    operations = [
        migrations.AddField(
            model_name='platform',
            name='specie',
            field=models.CharField(default='human', max_length=127),
        ),
        migrations.AlterField(
            model_name='platformprobe',
            name='platform',
            field=models.ForeignKey(related_name='probes', blank=True, to='legacy.Platform', null=True),
        ),
    ]
