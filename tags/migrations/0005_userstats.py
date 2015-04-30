# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '__first__'),
        ('tags', '0004_validation_stats'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserStats',
            fields=[
                ('user', models.OneToOneField(primary_key=True, serialize=False, to='legacy.AuthUser')),
                ('serie_tags', models.IntegerField(default=0)),
                ('sample_tags', models.IntegerField(default=0)),
                ('serie_validations', models.IntegerField(default=0)),
                ('sample_validations', models.IntegerField(default=0)),
                ('serie_validations_concordant', models.IntegerField(default=0)),
                ('sample_validations_concordant', models.IntegerField(default=0)),
                ('samples_to_pay_for', models.IntegerField(default=0)),
                ('samples_payed', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
