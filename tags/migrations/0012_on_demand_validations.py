# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0011_remove_userstats_samples_payed'),
    ]

    operations = [
        migrations.AddField(
            model_name='serievalidation',
            name='annotation_kappa',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='serievalidation',
            name='best_kappa',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='serievalidation',
            name='on_demand',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
