# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import migrations_plus


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0009_complex_earnings'),
    ]

    operations = [
        migrations_plus.RunSQL("""
            update tags_userstats set earned = earned_sample_annotations * 0.05,
                                      payed = samples_payed * 0.05;
        """)
    ]
