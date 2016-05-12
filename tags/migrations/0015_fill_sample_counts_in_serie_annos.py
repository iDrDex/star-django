# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


FILL_SQL = '''
    UPDATE series_annotation A SET samples = B.samples
    FROM (SELECT serie_annotation_id, count(*) as samples
          FROM sample_annotation group by 1) B
    WHERE A.id = B.serie_annotation_id;
'''


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0014_serieannotation_samples'),
    ]

    operations = [
        migrations.RunSQL(FILL_SQL),
    ]
