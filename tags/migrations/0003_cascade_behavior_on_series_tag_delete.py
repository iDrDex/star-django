# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0002_load_validations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serievalidation',
            name='series_tag',
            field=models.ForeignKey(related_name='validations', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='legacy.SeriesTag', null=True),
            preserve_default=True,
        ),

        migrations.RunSQL(
            """
                ALTER TABLE validation_job
                    DROP CONSTRAINT validation_job_series_tag_id_753f178d05a7d70f_fk_series_tag_id;
                ALTER TABLE validation_job
                    ADD CONSTRAINT validation_job_series_tag_id_753f178d05a7d70f_fk_series_tag_id
                    FOREIGN KEY (series_tag_id) REFERENCES series_tag (id) ON DELETE CASCADE;
            """,
            reverse_sql="""
                ALTER TABLE validation_job
                    DROP CONSTRAINT validation_job_series_tag_id_753f178d05a7d70f_fk_series_tag_id;
                ALTER TABLE validation_job
                    ADD CONSTRAINT validation_job_series_tag_id_753f178d05a7d70f_fk_series_tag_id
                    FOREIGN KEY (series_tag_id) REFERENCES series_tag (id);
            """
        ),

        migrations.RunSQL(
            """
                ALTER TABLE series_validation
                    DROP CONSTRAINT series_validati_series_tag_id_5a35d6201a93f3ec_fk_series_tag_id;
                ALTER TABLE series_validation
                    ADD CONSTRAINT series_validati_series_tag_id_5a35d6201a93f3ec_fk_series_tag_id
                    FOREIGN KEY (series_tag_id) REFERENCES series_tag (id) ON DELETE SET NULL;
            """,
            reverse_sql="""
                ALTER TABLE series_validation
                    DROP CONSTRAINT series_validati_series_tag_id_5a35d6201a93f3ec_fk_series_tag_id;
                ALTER TABLE series_validation
                    ADD CONSTRAINT series_validati_series_tag_id_5a35d6201a93f3ec_fk_series_tag_id
                    FOREIGN KEY (series_tag_id) REFERENCES series_tag (id);
            """
        ),

    ]
