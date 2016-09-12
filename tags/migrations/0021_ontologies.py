# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0020_serieannotation_captive'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='concept_full_id',
            field=models.CharField(max_length=512, blank=True),
        ),
        migrations.AddField(
            model_name='tag',
            name='concept_name',
            field=models.CharField(max_length=512, blank=True),
        ),
        migrations.AddField(
            model_name='tag',
            name='ontology_id',
            field=models.CharField(max_length=127, blank=True),
        ),
    ]
