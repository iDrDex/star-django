from funcy import project

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from handy.db import fetch_dicts


class Command(BaseCommand):
    help = 'Transfers users from web2py database'

    def handle(self, *args, **options):
        existings_ids = set(User.objects.values_list('id', flat=True))
        rows = fetch_dicts('select * from auth_user order by id')
        for row in rows:
            if row['id'] in existings_ids:
                continue
            user = User.objects.create_user(
                username=row['email'],
                **project(row, ['id', 'email', 'first_name', 'last_name'])
            )
            if user.id in {1, 24}:
                user.is_staff = True
                user.is_superuser = True
                user.save()
