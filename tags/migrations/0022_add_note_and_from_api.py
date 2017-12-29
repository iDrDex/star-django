# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0021_ontologies'),
    ]

    operations = [
        migrations.AddField(
            model_name='seriestag',
            name='note',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='seriestag',
            name='from_api',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='serievalidation',
            name='note',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='serievalidation',
            name='from_api',
            field=models.BooleanField(default=False),
        ),
    ]
