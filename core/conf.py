import redis

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


# Connecting to redis
try:
    redis_conf = settings.REDIS
except AttributeError:
    raise ImproperlyConfigured('You must specify non-empty REDIS setting to use cacheops')

redis_client = redis.StrictRedis(**redis_conf)
