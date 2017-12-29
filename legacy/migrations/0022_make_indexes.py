# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0021_nulls_and_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metaanalysis',
            name='analysis',
            field=models.ForeignKey(to='legacy.Analysis'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='series',
            field=models.ForeignKey(related_name='samples', to='legacy.Series'),
        ),
    ]
