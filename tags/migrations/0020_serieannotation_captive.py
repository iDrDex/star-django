# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0019_serievalidation_by_incompetent'),
    ]

    operations = [
        migrations.AddField(
            model_name='serieannotation',
            name='captive',
            field=models.BooleanField(default=False),
        ),
    ]
