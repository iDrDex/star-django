# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0016_platform_stats'),
    ]

    operations = [
        migrations.AddField(
            model_name='platform',
            name='verdict',
            field=models.CharField(max_length=127, blank=True),
        ),
    ]
