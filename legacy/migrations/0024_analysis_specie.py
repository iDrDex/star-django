# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0023_series_specie'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='specie',
            field=models.CharField(blank=True, max_length=127, choices=[('human', 'human'), ('mouse', 'mouse'), ('rat', 'rat')]),
        ),
    ]
