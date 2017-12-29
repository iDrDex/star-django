# -*- coding: utf-8 -*-


from django.db import migrations, models
import s3field.fields
import handy.models.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tags', '0023_fix_tags_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='Snapshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.TextField(default=b'', blank=True)),
                ('description', models.TextField(default=b'', blank=True)),
                ('metadata', handy.models.fields.JSONField(default={})),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('frozen', models.BooleanField(default=False)),
                ('frozen_on', models.DateTimeField(null=True, blank=True)),
                ('files', s3field.fields.S3MultiField()),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'snapshot',
            },
        ),
    ]
