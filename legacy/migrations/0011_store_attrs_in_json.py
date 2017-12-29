# -*- coding: utf-8 -*-


from django.db import migrations, models
import handy.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0010_move_tag_tables_out'),
    ]

    operations = [
        migrations.AddField(
            model_name='sample',
            name='attrs',
            field=handy.models.fields.JSONField(default={}),
        ),
        migrations.AddField(
            model_name='series',
            name='attrs',
            field=handy.models.fields.JSONField(default={}),
        ),
    ]
