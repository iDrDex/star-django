# -*- coding: utf-8 -*-


from django.db import migrations, models
import s3field.fields


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0002_rebind_user_fks'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='df',
            field=s3field.fields.S3Field(null=True),
        ),
    ]
