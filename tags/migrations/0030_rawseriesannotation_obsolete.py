# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0029_seriesannotation_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='rawseriesannotation',
            name='obsolete',
            field=models.BooleanField(default=False),
        ),
    ]
