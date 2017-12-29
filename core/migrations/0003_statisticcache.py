# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_user_competent'),
    ]

    operations = [
        migrations.CreateModel(
            name='StatisticCache',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.CharField(unique=True, max_length=30, db_index=True)),
                ('count', models.PositiveIntegerField(default=0)),
            ],
        ),
    ]
