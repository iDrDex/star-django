# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import handy.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0006_payments'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='extra',
            field=handy.models.fields.JSONField(default={}),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='payment',
            name='state',
            field=models.IntegerField(default=2, choices=[(1, b'pending'), (2, b'done'), (3, b'failed')]),
            preserve_default=False,
        ),
    ]
