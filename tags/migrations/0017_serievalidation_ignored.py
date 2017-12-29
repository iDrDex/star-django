# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0016_rebind_user_fks'),
    ]

    operations = [
        migrations.AddField(
            model_name='serievalidation',
            name='ignored',
            field=models.BooleanField(default=False),
        ),
    ]
