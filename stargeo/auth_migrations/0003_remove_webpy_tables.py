# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0002_django_18_changes'),
    ]

    operations = [
        migrations.RunSQL('''
            drop table auth_event;
            drop table auth_permission;
            drop table auth_membership;
            drop table auth_group;
            drop table auth_cas;
        ''')
    ]
