# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


FILL_SQL = '''
    INSERT INTO validation_job (series_tag_id)
    SELECT id FROM series_tag
'''

EMPTY_SQL = '''
    DELETE FROM validation_job;
'''


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(FILL_SQL, reverse_sql=EMPTY_SQL),
    ]
