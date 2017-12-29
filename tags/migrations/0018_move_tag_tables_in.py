# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0009_drop_legacy_user_prepare_to_move_tag_tables'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tags', '0017_serievalidation_ignored'),
    ]

    operations = [
        # Faking create, just moved models from legacy app
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='SampleTag',
                    fields=[
                        ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                        ('annotation', models.TextField(blank=True)),
                        ('is_active', models.BooleanField(default=True)),
                        ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                        ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                        ('created_by', models.ForeignKey(related_name='sample_annotations', db_column=b'created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                        ('modified_by', models.ForeignKey(related_name='+', db_column=b'modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                        ('sample', models.ForeignKey(blank=True, to='legacy.Sample', null=True)),
                    ],
                    options={
                        'db_table': 'sample_tag',
                    },
                ),
                migrations.CreateModel(
                    name='SeriesTag',
                    fields=[
                        ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                        ('header', models.CharField(max_length=512, blank=True)),
                        ('regex', models.CharField(max_length=512, blank=True)),
                        ('is_active', models.BooleanField(default=True)),
                        ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                        ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                        ('agreed', models.IntegerField(null=True, blank=True)),
                        ('fleiss_kappa', models.FloatField(null=True, blank=True)),
                        ('created_by', models.ForeignKey(related_name='serie_annotations', db_column=b'created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                        ('modified_by', models.ForeignKey(related_name='+', db_column=b'modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                        ('platform', models.ForeignKey(blank=True, to='legacy.Platform', null=True)),
                        ('series', models.ForeignKey(blank=True, to='legacy.Series', null=True)),
                    ],
                    options={
                        'db_table': 'series_tag',
                    },
                ),
                migrations.CreateModel(
                    name='Tag',
                    fields=[
                        ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                        ('tag_name', models.CharField(max_length=512)),
                        ('description', models.CharField(max_length=512, blank=True)),
                        ('is_active', models.BooleanField(default=True)),
                        ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                        ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                        ('created_by', models.ForeignKey(related_name='tags', db_column=b'created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                        ('modified_by', models.ForeignKey(related_name='+', db_column=b'modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                    ],
                    options={
                        'db_table': 'tag',
                    },
                ),
                migrations.AlterField(
                    model_name='serieannotation',
                    name='series_tag',
                    field=models.OneToOneField(related_name='canonical', to='tags.SeriesTag'),
                ),
                migrations.AlterField(
                    model_name='serieannotation',
                    name='tag',
                    field=models.ForeignKey(blank=True, to='tags.Tag', null=True),
                ),
                migrations.AlterField(
                    model_name='serievalidation',
                    name='series_tag',
                    field=models.ForeignKey(related_name='validations', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='tags.SeriesTag', null=True),
                ),
                migrations.AlterField(
                    model_name='serievalidation',
                    name='tag',
                    field=models.ForeignKey(related_name='validations', to='tags.Tag'),
                ),
                migrations.AlterField(
                    model_name='validationjob',
                    name='series_tag',
                    field=models.ForeignKey(to='tags.SeriesTag'),
                ),
                migrations.AddField(
                    model_name='seriestag',
                    name='tag',
                    field=models.ForeignKey(blank=True, to='tags.Tag', null=True),
                ),
                migrations.AddField(
                    model_name='sampletag',
                    name='series_tag',
                    field=models.ForeignKey(related_name='sample_tags', blank=True, to='tags.SeriesTag', null=True),
                ),
            ]
        )
    ]
