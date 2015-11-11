# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import s3field.fields


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0003_analysis_df'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='fold_changes',
            field=s3field.fields.S3Field(null=True),
        ),
    ]
