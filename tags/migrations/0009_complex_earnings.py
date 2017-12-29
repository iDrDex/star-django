# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0008_validations_crosscheck'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userstats',
            old_name='samples_to_pay_for',
            new_name='earned_sample_annotations',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='samples',
        ),
        migrations.AddField(
            model_name='userstats',
            name='earned',
            field=models.DecimalField(default=0, max_digits=8, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userstats',
            name='earned_sample_validations',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userstats',
            name='payed',
            field=models.DecimalField(default=0, max_digits=8, decimal_places=2),
            preserve_default=True,
        ),
    ]
