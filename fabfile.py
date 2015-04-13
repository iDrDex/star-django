# encoding: utf-8
from itertools import chain

from fabric.api import *
from fabric.contrib import django
from fabric.colors import green, cyan, red, yellow


__all__ = ('deploy', 'dirty_deploy', 'dirty_fast', 'shell',
           'restart', 'manage', 'incoming_files', 'install_requirements', 'migrate')


django.project('stargeo')
env.cwd = '/home/ubuntu/app'
env.use_ssh_config = True
env.hosts = ['stargeo']
# env.shell = 'DJANGO_SETTINGS_MODULE=threatmonitor.settings.production /bin/bash -l -O extglob -c'
activate = lambda: prefix('source ~/venv/bin/activate')


class FileSet(frozenset):
    @property
    def need_migrate(self):
        return self.need_upgrade or any('migrations' in filename for filename in self)

    @property
    def need_upgrade(self):
        return 'requirements.txt' in self

    @property
    def crontab_changed(self):
        return 'stuff/crontab.txt' in self


def restart():
    run('touch uwsgi-reload')


def collect_static():
    execute(manage, 'collectstatic --noinput')


def migrate():
    execute(manage, 'migrate')
    execute(manage, 'migrate --database=legacy')


def manage(cmd):
    with activate():
        run('./manage.py %s' % cmd)

def shell():
    with activate():
        run('./manage.py shell')

def incoming_files():
    return run('git --no-pager diff --name-only origin..HEAD',
               quiet=True).splitlines()


def install_requirements():
    with activate():
        with shell_env(PIP_DOWNLOAD_CACHE='~/.pip_download_cache'):
            run('pip install --exists-action=s -r requirements.txt')


def install_crontab():
    run('crontab stuff/crontab.txt')


def deploy():
    print(green('Fetching git commits...'))
    run('git fetch --progress')

    incoming = FileSet(chain(*execute(incoming_files).values()))

    if not incoming:
        print(yellow('Nothing seems to be changed, proceeding anyway'))

    print(green('Updating the working copy...'))
    result = run('git merge origin/master', warn_only=True)

    if result.return_code != 0:
        print(red('Git merge returned error, exiting'))
        raise SystemExit()

    if incoming.need_upgrade:
        print(green('Installing required Python libraries...'))
        execute(install_requirements)

    if incoming.need_migrate:
        print(green('Running migrations...'))
        execute(migrate)

    print(green('Collecting static files...'))
    execute(collect_static)

    if incoming.crontab_changed:
        print(green('Installing new crontab...'))
        execute(install_crontab)

    print(green('Reloading uWSGI...'))
    execute(restart)


def dirty_deploy():
    print(green('Uploading files...'))
    local("rsync -avzL --progress --filter=':- .gitignore' . stargeo:/home/ubuntu/app")

    print(green('Installing required Python libraries...'))
    execute(install_requirements)

    print(green('Running migrations...'))
    execute(migrate)

    print(green('Collecting static files...'))
    execute(collect_static)

    print(green('Reloading uWSGI...'))
    execute(restart)


def dirty_fast():
    print(green('Uploading files...'))
    local("rsync -avzL --progress --filter=':- .gitignore' . stargeo:/home/ubuntu/app")

    print(green('Reloading uWSGI...'))
    execute(restart)
