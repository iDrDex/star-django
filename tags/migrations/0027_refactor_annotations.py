# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0030_update_attrs'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tags', '0026_rename_serie_annotation'),
    ]

    operations = [
        migrations.CreateModel(
            name='RawSampleAnnotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('annotation', models.TextField(default=b'', blank=True)),
                ('sample', models.ForeignKey(to='legacy.Sample')),
            ],
            options={
                'db_table': 'raw_sample_annotation',
            },
        ),
        migrations.CreateModel(
            name='RawSeriesAnnotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('column', models.CharField(max_length=512, blank=True)),
                ('regex', models.CharField(max_length=512, blank=True)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('on_demand', models.BooleanField(default=False)),
                ('ignored', models.BooleanField(default=False)),
                ('by_incompetent', models.BooleanField(default=False)),
                ('from_api', models.BooleanField(default=False)),
                ('note', models.TextField(default=b'', blank=True)),
                ('accounted_for', models.BooleanField(default=False)),
                ('best_kappa', models.FloatField(null=True, blank=True)),
                ('agrees_with', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='tags.RawSeriesAnnotation', null=True)),
            ],
            options={
                'db_table': 'raw_series_annotation',
            },
        ),
        migrations.RenameField(
            model_name='seriesannotation',
            old_name='header',
            new_name='column',
        ),
        migrations.AddField(
            model_name='validationjob',
            name='annotation',
            field=models.ForeignKey(to='tags.SeriesAnnotation', null=True),
        ),
        migrations.AlterField(
            model_name='seriesannotation',
            name='created_on',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='seriesannotation',
            name='modified_on',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='rawseriesannotation',
            name='canonical',
            field=models.ForeignKey(related_name='raw_annotations', to='tags.SeriesAnnotation'),
        ),
        migrations.AddField(
            model_name='rawseriesannotation',
            name='created_by',
            field=models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='rawseriesannotation',
            name='from_series_tag',
            field=models.ForeignKey(to='tags.SeriesTag', null=True),
        ),
        migrations.AddField(
            model_name='rawseriesannotation',
            name='from_validation',
            field=models.ForeignKey(to='tags.SerieValidation', null=True),
        ),
        migrations.AddField(
            model_name='rawseriesannotation',
            name='platform',
            field=models.ForeignKey(to='legacy.Platform'),
        ),
        migrations.AddField(
            model_name='rawseriesannotation',
            name='series',
            field=models.ForeignKey(to='legacy.Series'),
        ),
        migrations.AddField(
            model_name='rawseriesannotation',
            name='tag',
            field=models.ForeignKey(to='tags.Tag'),
        ),
        migrations.AddField(
            model_name='rawsampleannotation',
            name='series_annotation',
            field=models.ForeignKey(related_name='sample_annotations', to='tags.RawSeriesAnnotation'),
        ),
        migrations.RunSQL(
            """create unique index raw_series_annotation_srcidx
               on raw_series_annotation (series_id, platform_id, tag_id, created_by_id)
               where is_active and not on_demand""",
            "drop index raw_series_annotation_srcidx",
        ),
    ]
