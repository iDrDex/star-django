import os

if os.environ.get('DJANGO_SETTINGS_MODULE'):
    from django.contrib.auth.models import User, Group, Permission
    User._meta.get_field('username').max_length = 127
    User._meta.db_table = 'dauth_user'
    User.groups.through._meta.db_table = 'dauth_user_groups'
    User.user_permissions.through._meta.db_table = 'dauth_user_user_permissions'
    Group._meta.db_table = 'dauth_group'
    Group.permissions.through._meta.db_table = 'dauth_group_permissions'
    Permission._meta.db_table = 'dauth_permission'
