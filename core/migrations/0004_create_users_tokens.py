# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import binascii

from django.db import migrations


def forwards_func(apps, schema_editor):
    User = apps.get_model('core', 'User')
    Token = apps.get_model('authtoken', 'Token')
    for user in User.objects.all().iterator():
        Token.objects.get_or_create(
            user=user,
            defaults=dict(key=binascii.hexlify(os.urandom(20)).decode()))

def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_statisticcache'),
        ('authtoken', '0002_auto_20160226_1747'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
