# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0010_fill_earnings'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userstats',
            name='samples_payed',
        ),
    ]
