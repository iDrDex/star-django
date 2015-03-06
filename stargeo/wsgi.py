"""
WSGI config for stargeo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
import honcho.environ


def load_env(filename):
    manage_dir = os.path.dirname(__file__)
    env_file = os.path.join(manage_dir, filename)

    env = honcho.environ.parse(open(env_file).read())
    for key, value in env.items():
        os.environ.setdefault(key, value)


load_env('../.env')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stargeo.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
