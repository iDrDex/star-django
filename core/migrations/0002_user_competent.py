# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_competent',
            field=models.BooleanField(default=False),
        ),
        migrations.RunSQL('update auth_user set is_competent = true'),
    ]
