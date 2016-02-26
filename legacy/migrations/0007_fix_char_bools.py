# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0006_fill_analysis_success'),
    ]

    operations = [
        migrations.RunSQL(
            """
                alter table analysis alter is_active type boolean
                    using coalesce(deleted, 'F') != 'T';
                alter table analysis alter is_active set not null;
                alter table analysis drop deleted;
            """,
            state_operations=[
                migrations.AlterField(
                    model_name='analysis',
                    name='is_active',
                    field=models.BooleanField(default=True),
                ),
                migrations.RemoveField(
                    model_name='analysis',
                    name='deleted',
                ),
            ]
        ),
        migrations.RunSQL(
            """
                alter table sample_tag alter is_active type boolean
                    using coalesce(is_active, 'F') = 'T';
                alter table sample_tag alter is_active set not null;
            """,
            state_operations=[
                migrations.AlterField(
                    model_name='sampletag',
                    name='is_active',
                    field=models.BooleanField(default=True),
                ),
            ]
        ),
        migrations.RunSQL(
            """
                alter table series_tag alter is_active type boolean
                    using coalesce(is_active, 'F') = 'T';
                alter table series_tag alter is_active set not null;
            """,
            state_operations=[
                migrations.AlterField(
                    model_name='seriestag',
                    name='is_active',
                    field=models.BooleanField(default=True),
                ),
            ]
        ),
        migrations.RunSQL(
            """
                alter table tag alter is_active type boolean
                    using coalesce(is_active, 'F') = 'T';
                alter table tag alter is_active set not null;
            """,
            state_operations=[
                migrations.AlterField(
                    model_name='tag',
                    name='is_active',
                    field=models.BooleanField(default=True),
                ),
            ]
        ),
        # migrations.RunSQL(
        #     """
        #         alter table sample add column is_active boolean not null default true;
        #         update sample set is_active = coalesce(deleted, 'F') != 'T';
        #         alter table sample drop deleted;
        #     """,
        #     state_operations=[
        #         migrations.AlterField(
        #             model_name='sample',
        #             name='is_active',
        #             field=models.BooleanField(default=True),
        #         ),
        #         migrations.RemoveField(
        #             model_name='sample',
        #             name='deleted',
        #         ),
        #     ]
        # ),
        migrations.RemoveField(
            model_name='seriestag',
            name='show_invariant'
        ),
        # Just use is_active for this
        migrations.RemoveField(
            model_name='seriestag',
            name='obsolete'
        ),
    ]
