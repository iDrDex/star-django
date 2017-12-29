# -*- coding: utf-8 -*-


from django.db import migrations, models
import handy.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0018_fill_platform_verdict'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='platform',
            name='datafile',
        ),
        migrations.RemoveField(
            model_name='platform',
            name='identifier',
        ),
        migrations.RemoveField(
            model_name='platform',
            name='scopes',
        ),
        migrations.AddField(
            model_name='platform',
            name='history',
            field=handy.models.fields.JSONField(default=[]),
        ),
        migrations.AddField(
            model_name='platform',
            name='probes_matched',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='platform',
            name='probes_total',
            field=models.IntegerField(null=True),
        ),
    ]
