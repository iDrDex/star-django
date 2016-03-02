# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0009_drop_legacy_user_prepare_to_move_tag_tables'),
        ('tags', '0018_move_tag_tables_in'),
    ]

    operations = [
        # Faking delete, cause we really just moving models to other app
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(
                    name='SeriesTag',
                ),
                migrations.DeleteModel(
                    name='Tag',
                ),
            ]
        )
    ]
