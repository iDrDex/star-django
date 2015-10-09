import os

if os.environ.get('DJANGO_SETTINGS_MODULE'):
    from django.contrib.auth.models import User, Group, Permission
    User._meta.db_table = 'dauth_user'
    Group._meta.db_table = 'dauth_group'
    Permission._meta.db_table = 'dauth_permission'
