from django.contrib.auth.models import AbstractUser


AbstractUser._meta.get_field('username').max_length = 127


class User(AbstractUser):
    class Meta:
        db_table = 'auth_user'
