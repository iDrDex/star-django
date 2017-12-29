# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0003_cascade_behavior_on_series_tag_delete'),
    ]

    operations = [
        migrations.AddField(
            model_name='samplevalidation',
            name='concordant',
            field=models.NullBooleanField(),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='serievalidation',
            name='samples_concordancy',
            field=models.FloatField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='serievalidation',
            name='samples_concordant',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='serievalidation',
            name='samples_total',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='samplevalidation',
            name='serie_validation',
            field=models.ForeignKey(related_name='sample_validations', to='tags.SerieValidation'),
            preserve_default=True,
        ),
    ]
