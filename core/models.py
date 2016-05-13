from django.db import models
from django.contrib.auth.models import AbstractUser


AbstractUser._meta.get_field('username').max_length = 127


class User(AbstractUser):
    is_competent = models.BooleanField(default=False)

    class Meta:
        db_table = 'auth_user'
