# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def fill_verdict(apps, schema_editor):
    Platform = apps.get_model("legacy", "Platform")
    for platform in Platform.objects.iterator():
        platform.datafile = platform.datafile or ''  # fix nulls

        if platform.datafile.startswith('/'):
            platform.verdict = 'ok'
            if not platform.stats:
                platform.stats['files'] = [platform.datafile]
            platform.save()
        elif platform.datafile.startswith('<'):
            platform.verdict = platform.datafile[1:-1]
            platform.save()


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0017_platform_verdict'),
    ]

    operations = [
        migrations.RunPython(fill_verdict),
    ]
