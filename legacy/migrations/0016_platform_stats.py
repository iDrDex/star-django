# -*- coding: utf-8 -*-


from django.db import migrations, models
import handy.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0015_add_platform_specie'),
    ]

    operations = [
        migrations.AddField(
            model_name='platform',
            name='last_filled',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='platform',
            name='stats',
            field=handy.models.fields.JSONField(default={}),
        ),
    ]
