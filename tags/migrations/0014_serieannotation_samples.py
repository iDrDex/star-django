# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0013_canonical_annotations'),
    ]

    operations = [
        migrations.AddField(
            model_name='serieannotation',
            name='samples',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
