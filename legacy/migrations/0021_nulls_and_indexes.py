# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0020_fix_fts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metaanalysis',
            name='analysis',
            field=models.ForeignKey(to='legacy.Analysis', db_index=False),
        ),
        migrations.AlterField(
            model_name='metaanalysis',
            name='casedatacount',
            field=models.IntegerField(verbose_name='cases'),
        ),
        migrations.AlterField(
            model_name='metaanalysis',
            name='controldatacount',
            field=models.IntegerField(verbose_name='controls'),
        ),
        migrations.AlterField(
            model_name='metaanalysis',
            name='direction',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='metaanalysis',
            name='k',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='metaanalysis',
            name='mygene_entrez',
            field=models.IntegerField(verbose_name='entrez'),
        ),
        migrations.AlterField(
            model_name='metaanalysis',
            name='mygene_sym',
            field=models.CharField(max_length=512, verbose_name='sym'),
        ),
        migrations.AlterField(
            model_name='platform',
            name='gpl_name',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='platformprobe',
            name='mygene_entrez',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='platformprobe',
            name='mygene_sym',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='platformprobe',
            name='platform',
            field=models.ForeignKey(related_name='probes', to='legacy.Platform'),
        ),
        migrations.AlterField(
            model_name='platformprobe',
            name='probe',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='sample',
            name='gsm_name',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='sample',
            name='platform',
            field=models.ForeignKey(to='legacy.Platform', db_index=False),
        ),
        migrations.AlterField(
            model_name='sample',
            name='series',
            field=models.ForeignKey(related_name='samples', to='legacy.Series', db_index=False),
        ),
        migrations.AlterField(
            model_name='series',
            name='gse_name',
            field=models.TextField(),
        ),
    ]
