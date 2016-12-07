# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0022_make_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='specie',
            field=models.CharField(max_length=127, blank=True),
        ),
    ]
