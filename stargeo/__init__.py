import os
import honcho.environ


def load_env(filename):
    manage_dir = os.path.dirname(__file__)
    env_file = os.path.join(manage_dir, filename)

    env = honcho.environ.parse(open(env_file).read())
    for key, value in env.items():
        os.environ.setdefault(key, value)


if 'SECRET_KEY' not in os.environ:
    load_env('../.env')


if os.environ.get('DJANGO_SETTINGS_MODULE'):
    from django.contrib.auth.models import User, Group, Permission
    User._meta.get_field('username').max_length = 127
    User._meta.db_table = 'dauth_user'
    User.groups.through._meta.db_table = 'dauth_user_groups'
    User.user_permissions.through._meta.db_table = 'dauth_user_user_permissions'
    Group._meta.db_table = 'dauth_group'
    Group.permissions.through._meta.db_table = 'dauth_group_permissions'
    Permission._meta.db_table = 'dauth_permission'
