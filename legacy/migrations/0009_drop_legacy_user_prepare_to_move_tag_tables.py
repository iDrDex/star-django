# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0008_allow_nonunique_deleted_tags'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AuthUser',
        ),
        # Faking delete, cause we really just moving models to other app
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(
                    model_name='sampletag',
                    name='created_by',
                ),
                migrations.RemoveField(
                    model_name='sampletag',
                    name='modified_by',
                ),
                migrations.RemoveField(
                    model_name='sampletag',
                    name='sample',
                ),
                migrations.RemoveField(
                    model_name='sampletag',
                    name='series_tag',
                ),
                migrations.RemoveField(
                    model_name='seriestag',
                    name='created_by',
                ),
                migrations.RemoveField(
                    model_name='seriestag',
                    name='modified_by',
                ),
                migrations.RemoveField(
                    model_name='seriestag',
                    name='platform',
                ),
                migrations.RemoveField(
                    model_name='seriestag',
                    name='series',
                ),
                migrations.RemoveField(
                    model_name='seriestag',
                    name='tag',
                ),
                migrations.RemoveField(
                    model_name='tag',
                    name='created_by',
                ),
                migrations.RemoveField(
                    model_name='tag',
                    name='modified_by',
                ),
                migrations.DeleteModel(
                    name='SampleTag',
                ),
            ]
        )
    ]
