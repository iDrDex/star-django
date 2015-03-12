# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import migrations_plus


FILL_SQL = '''
    INSERT INTO validation_job (series_tag_id)
    SELECT id FROM series_tag
'''

EMPTY_SQL = 'SELECT 1'


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0001_initial'),
    ]

    operations = [
        # Do it twice cause we need 2 validation jobs for each annotation
        migrations_plus.RunSQL(FILL_SQL, reverse_sql=EMPTY_SQL, db='legacy'),
        migrations_plus.RunSQL(FILL_SQL, reverse_sql=EMPTY_SQL, db='legacy'),
    ]
