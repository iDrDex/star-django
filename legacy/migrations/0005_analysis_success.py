# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0004_analysis_fold_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='success',
            field=models.BooleanField(default=False),
        ),
    ]
