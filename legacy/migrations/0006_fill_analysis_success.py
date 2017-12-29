# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0005_analysis_success'),
    ]

    operations = [
        migrations.RunSQL('''
            UPDATE analysis SET success = true
            WHERE id in (SELECT distinct analysis_id FROM meta_analysis)
        ''')
    ]
