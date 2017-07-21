# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0028_more_things'),
    ]

    operations = [
        migrations.AddField(
            model_name='seriesannotation',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
