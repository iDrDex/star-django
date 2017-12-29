# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0012_series_fts'),
    ]

    operations = [
        # Don't want to bother database as db field is not really changed, the related_name did
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='sample',
                    name='series',
                    field=models.ForeignKey(related_name='samples', blank=True, to='legacy.Series', null=True),
                ),
            ],
            database_operations=[]
        )
    ]
