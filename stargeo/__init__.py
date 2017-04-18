import os
import honcho.environ
from .celery import app as celery_app  # noqa


def load_env(filename):
    manage_dir = os.path.dirname(__file__)
    env_file = os.path.join(manage_dir, filename)

    env = honcho.environ.parse(open(env_file).read())
    for key, value in env.items():
        os.environ.setdefault(key, value)


if 'SECRET_KEY' not in os.environ:
    load_env('../.env')
