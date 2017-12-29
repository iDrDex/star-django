# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0026_auto_20161207_1257'),
    ]

    operations = [
        migrations.RunSQL("""
drop index series_search_idx;
create index series_search_gin_idx on series using gin(tsv);
        """,

        reverse_sql="""
drop index series_search_gin_idx;
create index series_search_idx on series using gist(tsv);
        """)
    ]
