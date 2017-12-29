# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0028_drop_platformprobe_id'),
    ]

    operations = [
        migrations.RunSQL("""
            drop table balanced_meta;
            drop table count;
            drop table platform_stats;
            drop table sample_attribute_header;
            drop table sample_tag_view_results;
            drop table sample_validation__backup;
            drop table sample_view_annotation_filter;
            drop table sample_view_results;
            drop table scheduler_task cascade;
            drop table scheduler_task_deps;
            drop table scheduler_run;
            drop table scheduler_worker;
            drop table series_attribute_header;
            drop table series_tag_view_results;
            drop table series_view_results cascade;
            drop table user_search cascade;
            drop table search;
        """)
    ]


