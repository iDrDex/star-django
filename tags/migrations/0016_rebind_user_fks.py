# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0015_fill_sample_counts_in_serie_annos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='payment',
            name='receiver',
            field=models.ForeignKey(related_name='payments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='samplevalidation',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='serievalidation',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userstats',
            name='user',
            field=models.OneToOneField(related_name='stats', primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='validationjob',
            name='locked_by',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
