# -*- coding: utf-8 -*-


from django.db import migrations, models
import handy.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_create_users_tokens'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalCounter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField()),
                ('counters', handy.models.fields.JSONField()),
            ],
        ),
    ]
