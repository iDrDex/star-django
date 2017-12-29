# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0030_rawseriesannotation_obsolete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seriesannotation',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
