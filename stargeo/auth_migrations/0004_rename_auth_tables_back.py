# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    We used names prefixed with "d" to avoid clashes with web2py tables before.
    """

    dependencies = [
        ('auth', '0003_remove_webpy_tables'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='group',
            table=None,
        ),
        migrations.AlterModelTable(
            name='permission',
            table=None,
        ),
        migrations.AlterModelTable(
            name='user',
            table=None,
        ),
    ]
