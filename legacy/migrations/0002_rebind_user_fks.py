# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysis',
            name='created_by',
            field=models.ForeignKey(db_column='created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='analysis',
            name='modified_by',
            field=models.ForeignKey(related_name='+', db_column='modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='sampletag',
            name='created_by',
            field=models.ForeignKey(related_name='sample_annotations', db_column='created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='sampletag',
            name='modified_by',
            field=models.ForeignKey(related_name='+', db_column='modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='seriestag',
            name='created_by',
            field=models.ForeignKey(related_name='serie_annotations', db_column='created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='seriestag',
            name='modified_by',
            field=models.ForeignKey(related_name='+', db_column='modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='created_by',
            field=models.ForeignKey(related_name='tags', db_column='created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='modified_by',
            field=models.ForeignKey(related_name='+', db_column='modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
