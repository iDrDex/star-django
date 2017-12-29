# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0007_fix_char_bools'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='tag_name',
            field=models.CharField(max_length=512),
        ),
        migrations.RunSQL(
            "CREATE UNIQUE INDEX tag_name_idx ON tag (tag_name) WHERE is_active;",
            "DROP INDEX tag_name_idx",
        )
    ]
