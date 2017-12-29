# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('analysis_name', models.CharField(max_length=512)),
                ('description', models.CharField(default='', max_length=512, blank=True)),
                ('case_query', models.CharField(max_length=512)),
                ('control_query', models.CharField(max_length=512)),
                ('modifier_query', models.CharField(default='', max_length=512, blank=True)),
                ('min_samples', models.IntegerField(default=3, null=True, blank=True)),
                ('series_count', models.IntegerField(null=True, blank=True)),
                ('platform_count', models.IntegerField(null=True, blank=True)),
                ('sample_count', models.IntegerField(null=True, blank=True)),
                ('series_ids', models.TextField(blank=True)),
                ('platform_ids', models.TextField(blank=True)),
                ('sample_ids', models.TextField(blank=True)),
                ('is_active', models.CharField(max_length=1, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('deleted', models.CharField(max_length=1, null=True, blank=True)),
            ],
            options={
                'db_table': 'analysis',
            },
        ),
        migrations.CreateModel(
            name='AuthUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=128, blank=True)),
                ('last_name', models.CharField(max_length=128, blank=True)),
                ('email', models.CharField(max_length=512, blank=True)),
                ('password', models.CharField(max_length=512, blank=True)),
                ('registration_key', models.CharField(max_length=512, blank=True)),
                ('reset_password_key', models.CharField(max_length=512, blank=True)),
                ('registration_id', models.CharField(max_length=512, blank=True)),
            ],
            options={
                'db_table': 'auth_user',
            },
        ),
        migrations.CreateModel(
            name='MetaAnalysis',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mygene_sym', models.CharField(max_length=512, verbose_name='sym', blank=True)),
                ('mygene_entrez', models.IntegerField(null=True, verbose_name='entrez', blank=True)),
                ('direction', models.CharField(max_length=512, blank=True)),
                ('casedatacount', models.IntegerField(null=True, verbose_name='cases', blank=True)),
                ('controldatacount', models.IntegerField(null=True, verbose_name='controls', blank=True)),
                ('k', models.IntegerField(null=True, blank=True)),
                ('fixed_te', models.FloatField(null=True, blank=True)),
                ('fixed_se', models.FloatField(null=True, blank=True)),
                ('fixed_lower', models.FloatField(null=True, blank=True)),
                ('fixed_upper', models.FloatField(null=True, blank=True)),
                ('fixed_pval', models.FloatField(null=True, blank=True)),
                ('fixed_zscore', models.FloatField(null=True, blank=True)),
                ('random_te', models.FloatField(null=True, blank=True)),
                ('random_se', models.FloatField(null=True, blank=True)),
                ('random_lower', models.FloatField(null=True, blank=True)),
                ('random_upper', models.FloatField(null=True, blank=True)),
                ('random_pval', models.FloatField(null=True, blank=True)),
                ('random_zscore', models.FloatField(null=True, blank=True)),
                ('predict_te', models.FloatField(null=True, blank=True)),
                ('predict_se', models.FloatField(null=True, blank=True)),
                ('predict_lower', models.FloatField(null=True, blank=True)),
                ('predict_upper', models.FloatField(null=True, blank=True)),
                ('predict_pval', models.FloatField(null=True, blank=True)),
                ('predict_zscore', models.FloatField(null=True, blank=True)),
                ('tau2', models.FloatField(null=True, blank=True)),
                ('tau2_se', models.FloatField(null=True, blank=True)),
                ('c', models.FloatField(null=True, blank=True)),
                ('h', models.FloatField(null=True, blank=True)),
                ('h_lower', models.FloatField(null=True, blank=True)),
                ('h_upper', models.FloatField(null=True, blank=True)),
                ('i2', models.FloatField(null=True, blank=True)),
                ('i2_lower', models.FloatField(null=True, blank=True)),
                ('i2_upper', models.FloatField(null=True, blank=True)),
                ('q', models.FloatField(null=True, blank=True)),
                ('q_df', models.FloatField(null=True, blank=True)),
                ('analysis', models.ForeignKey(blank=True, to='legacy.Analysis', null=True)),
            ],
            options={
                'db_table': 'meta_analysis',
            },
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gpl_name', models.TextField(blank=True)),
                ('scopes', models.CharField(max_length=512, blank=True)),
                ('identifier', models.CharField(max_length=512, blank=True)),
                ('datafile', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'platform',
            },
        ),
        migrations.CreateModel(
            name='PlatformProbe',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('probe', models.TextField(blank=True)),
                ('mygene_sym', models.TextField(blank=True)),
                ('mygene_entrez', models.IntegerField(null=True, blank=True)),
                ('platform', models.ForeignKey(blank=True, to='legacy.Platform', null=True)),
            ],
            options={
                'db_table': 'platform_probe',
            },
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gsm_name', models.TextField(blank=True)),
                ('deleted', models.CharField(max_length=1, null=True, blank=True)),
                ('platform', models.ForeignKey(blank=True, to='legacy.Platform', null=True)),
            ],
            options={
                'db_table': 'sample',
            },
        ),
        migrations.CreateModel(
            name='SampleAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attribute_value', models.TextField(blank=True)),
                ('attribute_name', models.TextField(blank=True)),
                ('sample', models.ForeignKey(blank=True, to='legacy.Sample', null=True)),
            ],
            options={
                'db_table': 'sample_attribute',
            },
        ),
        migrations.CreateModel(
            name='SampleTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('annotation', models.TextField(blank=True)),
                ('is_active', models.CharField(default='T', max_length=1, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.ForeignKey(related_name='sample_annotations', db_column='created_by', blank=True, to='legacy.AuthUser', null=True)),
                ('modified_by', models.ForeignKey(related_name='+', db_column='modified_by', blank=True, to='legacy.AuthUser', null=True)),
                ('sample', models.ForeignKey(blank=True, to='legacy.Sample', null=True)),
            ],
            options={
                'db_table': 'sample_tag',
            },
        ),
        migrations.CreateModel(
            name='Series',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gse_name', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'series',
            },
        ),
        migrations.CreateModel(
            name='SeriesAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attribute_value', models.TextField(blank=True)),
                ('attribute_name', models.TextField(blank=True)),
                ('series', models.ForeignKey(blank=True, to='legacy.Series', null=True)),
            ],
            options={
                'db_table': 'series_attribute',
            },
        ),
        migrations.CreateModel(
            name='SeriesTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('header', models.CharField(max_length=512, blank=True)),
                ('regex', models.CharField(max_length=512, blank=True)),
                ('show_invariant', models.CharField(max_length=1, blank=True)),
                ('is_active', models.CharField(default='T', max_length=1, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('agreed', models.IntegerField(null=True, blank=True)),
                ('fleiss_kappa', models.FloatField(null=True, blank=True)),
                ('obsolete', models.CharField(max_length=1, null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='serie_annotations', db_column='created_by', blank=True, to='legacy.AuthUser', null=True)),
                ('modified_by', models.ForeignKey(related_name='+', db_column='modified_by', blank=True, to='legacy.AuthUser', null=True)),
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
                ('tag_name', models.CharField(unique=True, max_length=512, blank=True)),
                ('description', models.CharField(max_length=512, blank=True)),
                ('is_active', models.CharField(default='T', max_length=1, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.ForeignKey(related_name='tags', db_column='created_by', blank=True, to='legacy.AuthUser', null=True)),
                ('modified_by', models.ForeignKey(related_name='+', db_column='modified_by', blank=True, to='legacy.AuthUser', null=True)),
            ],
            options={
                'db_table': 'tag',
            },
        ),
        migrations.AddField(
            model_name='seriestag',
            name='tag',
            field=models.ForeignKey(blank=True, to='legacy.Tag', null=True),
        ),
        migrations.AddField(
            model_name='sampletag',
            name='series_tag',
            field=models.ForeignKey(related_name='sample_tags', blank=True, to='legacy.SeriesTag', null=True),
        ),
        migrations.AddField(
            model_name='sample',
            name='series',
            field=models.ForeignKey(blank=True, to='legacy.Series', null=True),
        ),
        migrations.AddField(
            model_name='analysis',
            name='created_by',
            field=models.ForeignKey(db_column='created_by', blank=True, to='legacy.AuthUser', null=True),
        ),
        migrations.AddField(
            model_name='analysis',
            name='modified_by',
            field=models.ForeignKey(related_name='+', db_column='modified_by', blank=True, to='legacy.AuthUser', null=True),
        ),
    ]
