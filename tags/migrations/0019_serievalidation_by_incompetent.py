# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0018_move_tag_tables_in'),
    ]

    operations = [
        migrations.AddField(
            model_name='serievalidation',
            name='by_incompetent',
            field=models.BooleanField(default=False),
        ),
    ]
