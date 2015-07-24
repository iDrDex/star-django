# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0007_payment_state_and_extra'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='serievalidation',
            name='samples_concordancy',
        ),
        migrations.AddField(
            model_name='serievalidation',
            name='agrees_with',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='tags.SerieValidation', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='validationjob',
            name='priority',
            field=models.FloatField(default=0),
            preserve_default=True,
        ),
    ]
