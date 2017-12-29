# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0009_complex_earnings'),
    ]

    operations = [
        migrations.RunSQL("""
            update tags_userstats set earned = earned_sample_annotations * 0.05,
                                      payed = samples_payed * 0.05;
        """)
    ]
