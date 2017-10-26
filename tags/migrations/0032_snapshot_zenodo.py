# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import handy.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0031_series_annos_active_by_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='snapshot',
            name='zenodo',
            field=handy.models.fields.JSONField(null=True),
        ),
    ]
