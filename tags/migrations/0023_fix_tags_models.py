# -*- coding: utf-8 -*-


from django.db import migrations, models
import handy.models.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0022_add_note_and_from_api'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sampleannotation',
            name='annotation',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='sampletag',
            name='annotation',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='samplevalidation',
            name='annotation',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='seriestag',
            name='note',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='serievalidation',
            name='note',
            field=models.TextField(default=b'', blank=True),
        ),
    ]
