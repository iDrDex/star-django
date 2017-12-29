# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0024_snapshot'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serieannotation',
            name='platform',
            field=models.ForeignKey(to='legacy.Platform'),
        ),
        migrations.AlterField(
            model_name='serieannotation',
            name='series',
            field=models.ForeignKey(to='legacy.Series'),
        ),
        migrations.AlterField(
            model_name='serieannotation',
            name='tag',
            field=models.ForeignKey(to='tags.Tag'),
        ),
    ]
