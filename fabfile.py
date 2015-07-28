# encoding: utf-8
from itertools import chain

from fabric.api import *
from fabric.contrib import django
from fabric.colors import green, cyan, red, yellow


__all__ = ('deploy', 'rsync', 'dirty_deploy', 'dirty_fast', 'shell',
           'restart', 'manage', 'incoming_files', 'install_requirements', 'migrate',
           'pull_db')


django.project('stargeo')
env.cwd = '/home/ubuntu/app'
env.use_ssh_config = True
env.hosts = ['stargeo']
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
    print(green('Restarting celery...'))
    sudo('supervisorctl restart celery')

    print(green('Reloading uWSGI...'))
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

    execute(restart)


def rsync():
    print(green('Uploading files...'))
    local("rsync -avzL --progress --filter=':- .gitignore' . stargeo:/home/ubuntu/app")


def dirty_deploy():
    execute(rsync)

    print(green('Installing required Python libraries...'))
    execute(install_requirements)

    print(green('Running migrations...'))
    execute(migrate)

    print(green('Collecting static files...'))
    execute(collect_static)

    execute(restart)


def dirty_fast():
    execute(rsync)

    # Not restarting celery, make `fab restart` if you do want that
    print(green('Reloading uWSGI...'))
    run('touch uwsgi-reload')


import os.path
import honcho.environ
import dj_database_url

def pull_db(dump='app'):
    app_env = honcho.environ.parse(open('.env').read())
    remote_db = dj_database_url.parse(app_env['REAL_LEGACY_DATABASE_URL'])
    local_db = dj_database_url.parse(app_env['LEGACY_DATABASE_URL'])

    # Make and download database dump
    if dump == 'direct':
        # Dump directly from remote database with local pg_dump
        print('Making database dump...')
        local('PGPASSWORD=%(PASSWORD)s pg_dump -vC -Upostgres -h %(HOST)s %(NAME)s > stargeo.sql'
                % remote_db)
    elif dump == 'app':
        # Alternative: dump to app-server than rsync here,
        #              useful with slow or flaky internet connection
        print('Making database dump...')
        run('PGPASSWORD=%(PASSWORD)s pg_dump -vC -Upostgres -h %(HOST)s %(NAME)s > stargeo.sql'
                % remote_db)
        print('Downloading dump...')
        local('rsync -avz --progress stargeo:/home/ubuntu/app/stargeo.sql stargeo.sql')
        run('rm stargeo.sql')
    elif dump == 'local':
        print('Using local dump...')
        if not os.path.exists('stargeo.sql'):
            print(red('Local database dump not found (stargeo.sql).\n'
                      'Please use "remote" or "app" dump.'))
            return

    print('Dropping %(NAME)s...' % local_db)
    local('psql -Upostgres -c "drop database if exists %(NAME)s"' % local_db)

    # Check if database is deleted
    with quiet():
        if local('psql -Upostgres -d %(NAME)s -c ""' % local_db, capture=True).succeeded:
            print(red('Database not dropped.\n'
                      'Disconnect all the clients and retry with "fab pull_db:local"'))
            return

    # Load dump
    local('psql -Upostgres -f stargeo.sql')
