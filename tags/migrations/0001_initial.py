# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='SampleValidation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('annotation', models.TextField(blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to='legacy.AuthUser')),
                ('sample', models.ForeignKey(blank=True, to='legacy.Sample', null=True)),
            ],
            options={
                'db_table': 'sample_validation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SerieValidation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('column', models.CharField(max_length=512, blank=True)),
                ('regex', models.CharField(max_length=512, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to='legacy.AuthUser')),
                ('platform', models.ForeignKey(related_name='validations', to='legacy.Platform')),
                ('series', models.ForeignKey(related_name='validations', to='legacy.Series')),
                ('series_tag', models.ForeignKey(related_name='validations', to='legacy.SeriesTag')),
                ('tag', models.ForeignKey(related_name='validations', to='legacy.Tag')),
            ],
            options={
                'db_table': 'series_validation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ValidationJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('locked_on', models.DateTimeField(null=True, blank=True)),
                ('locked_by', models.ForeignKey(blank=True, to='legacy.AuthUser', null=True)),
                ('series_tag', models.ForeignKey(to='legacy.SeriesTag')),
            ],
            options={
                'db_table': 'validation_job',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='samplevalidation',
            name='serie_validation',
            field=models.ForeignKey(to='tags.SerieValidation'),
            preserve_default=True,
        ),
    ]
