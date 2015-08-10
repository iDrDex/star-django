# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '__first__'),
        ('tags', '0012_on_demand_validations'),
    ]

    operations = [
        migrations.CreateModel(
            name='SampleAnnotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('annotation', models.TextField(blank=True)),
                ('sample', models.ForeignKey(to='legacy.Sample')),
            ],
            options={
                'db_table': 'sample_annotation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SerieAnnotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('header', models.CharField(max_length=512, blank=True)),
                ('regex', models.CharField(max_length=512, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('annotations', models.IntegerField()),
                ('authors', models.IntegerField()),
                ('fleiss_kappa', models.FloatField(null=True, blank=True)),
                ('best_cohens_kappa', models.FloatField(null=True, blank=True)),
                ('platform', models.ForeignKey(blank=True, to='legacy.Platform', null=True)),
                ('series', models.ForeignKey(blank=True, to='legacy.Series', null=True)),
                ('series_tag', models.OneToOneField(related_name='canonical', to='legacy.SeriesTag')),
                ('tag', models.ForeignKey(blank=True, to='legacy.Tag', null=True)),
            ],
            options={
                'db_table': 'series_annotation',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='sampleannotation',
            name='serie_annotation',
            field=models.ForeignKey(related_name='sample_annotations', to='tags.SerieAnnotation'),
            preserve_default=True,
        ),
    ]
