#!/usr/bin/env python
import os
import sys
import honcho.environ


def load_env():
    manage_dir = os.path.dirname(__file__)
    env_file = os.path.join(manage_dir, '.env')

    env = honcho.environ.parse(open(env_file).read())
    for key, value in env.items():
        os.environ.setdefault(key, value)


if __name__ == "__main__":
    load_env()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stargeo.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
