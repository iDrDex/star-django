# encoding: utf-8
from fabric.api import *
from fabric.contrib import django
from fabric.colors import green, red


__all__ = ('deploy', 'deploy_fast', 'rsync', 'dirty_deploy', 'dirty_fast',
           'shell', 'ssh', 'config',
           'restart', 'manage', 'install_requirements', 'migrate',
           'pull_db', 'set_things_up')


django.project('stargeo')
env.cwd = '/home/ubuntu/app'
env.use_ssh_config = True
env.hosts = ['sclone']
activate = lambda: prefix('source ~/venv/bin/activate')
node = lambda: prefix('source ~/.nvm/nvm.sh')


def restart():
    print(green('Restarting celery...'))
    sudo('supervisorctl restart celery')

    print(green('Reloading uWSGI...'))
    run('touch uwsgi-reload')


def collect_static():
    execute(manage, 'collectstatic --noinput')


def build_frontend():
    with cd('frontend'), node():
        run('npm install')
        run('npm run build')
        run('cp -r dist ../public')


def migrate():
    execute(manage, 'migrate')


def manage(cmd):
    with activate():
        run('./manage.py %s' % cmd)


def smart_shell(command=''):
    env_commands = "cd '%s'; %s" % (env.cwd, " && ".join(env.command_prefixes))
    open_shell('%s; %s' % (env_commands, command))

def shell():
    with activate():
        smart_shell('./manage.py shell')

def ssh(command=''):
    with activate():
        if command:
            run(command)
        else:
            smart_shell()

def config():
    local("vim sftp://%s/%s" % (env.host_string, 'app/.env'))


def install_requirements():
    with activate():
        run('pip install --exists-action=s -r requirements.txt')


def install_crontab():
    run('crontab stuff/crontab')


def deploy():
    print(green('Fetching git commits...'))
    run('git fetch --progress')

    print(green('Updating the working copy...'))
    result = run('git merge origin/master', warn_only=True)

    if result.return_code != 0:
        print(red('Git merge returned error, exiting'))
        raise SystemExit()

    print(green('Installing required Python libraries...'))
    execute(install_requirements)

    print(green('Running migrations...'))
    execute(migrate)

    print(green('Collecting static files...'))
    execute(collect_static)

    print(green('Building frontend...'))
    execute(build_frontend)

    print(green('Installing new crontab...'))
    execute(install_crontab)

    execute(restart)


def deploy_fast():
    print(green('Updating working copy...'))
    run('git pull origin master')

    # Not restarting celery, make `fab restart` if you do want that
    print(green('Reloading uWSGI...'))
    run('touch uwsgi-reload')


def rsync():
    print(green('Uploading files...'))
    local("rsync -avzL --progress --filter=':- .gitignore' -C . stargeo:/home/ubuntu/app")


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
    remote_db = dj_database_url.parse(app_env['REAL_DATABASE_URL'])
    local_db = dj_database_url.parse(app_env['DATABASE_URL'])

    DUMP_COMMAND = 'PGPASSWORD=%(PASSWORD)s pg_dump -vC -Upostgres -h %(HOST)s %(NAME)s ' \
                   '| gzip --fast --rsyncable > stargeo.sql.gz' % remote_db

    # Make and download database dump
    if dump == 'direct':
        # Dump directly from remote database with local pg_dump
        print('Making database dump...')
        local(DUMP_COMMAND)
    elif dump == 'app':
        # Alternative: dump to app-server than rsync here,
        #              useful with slow or flaky internet connection.
        print('Making database dump...')
        run(DUMP_COMMAND)
        print('Downloading dump...')
        local('rsync -av --progress stargeo:/home/ubuntu/app/stargeo.sql.gz stargeo.sql.gz')
        run('rm stargeo.sql.gz')
    elif dump == 'local':
        print('Using local dump...')
        if not os.path.exists('stargeo.sql.gz'):
            print(red('Local database dump not found (stargeo.sql.gz).\n'
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
    local('gzip -cd stargeo.sql.gz | psql -Upostgres -f -')


from fabric.contrib import files

def set_things_up():
    with cd('/home/ubuntu'):
        run('mkdir logs; chmod 777 logs;')
        run('git clone https://github.com/idrdex/star-django.git app')

    print(green('Installing packages...'))
    sudo('apt update')
    sudo('apt install --yes python2.7 python-pip virtualenv')
    sudo('apt install --yes --no-install-recommends r-base-core r-base-core-dev')
    sudo('apt install --yes redis-server')

    print(green('Configuring .env...'))
    # Generate SECRET_KEY
    from django.utils.crypto import get_random_string
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    secret_key = get_random_string(50, chars)
    files.upload_template('stuff/.env.prod', '.env', {'SECRET_KEY': secret_key},
        use_jinja=True, keep_trailing_newline=True)

    # Set up hosts
    files.append('/etc/hosts', ['127.0.0.1 db', '127.0.0.1 redis'], use_sudo=True)

    print(green('Setting up PostgreSQL...'))
    sudo('apt install --yes postgresql-9.5 libpq-dev')
    files.sed('/etc/postgresql/9.5/main/pg_hba.conf',
        '^(local.*|host\s+all\s+all\s+127\.0\.0\.1/32.*)(peer|md5)$', '\\1trust',
        use_sudo=True, shell=True)
    sudo('service postgresql reload')
    # TODO: configure postgres

    print(green('Creating database and running migrations...'))
    run('psql -Upostgres -f stuff/db-schema.sql')
    run('psql -Upostgres star -f stuff/db-migrations.sql')
    with activate():
        run('./manage.py migrate')

    print(green('Setting up Django server...'))
    sudo('apt install --yes uwsgi-emperor uwsgi-plugin-python')
    run('touch uwsgi-reload')
    files.upload_template('stuff/uwsgi-web.ini', '/etc/uwsgi-emperor/vassals/stargeo.ini',
        use_sudo=True, backup=False)
    sudo('service uwsgi-emperor reload')

    print(green('Configure nginx...'))
    sudo('apt install --yes nginx')
    sudo('rm /etc/nginx/sites-enabled/default')
    files.upload_template('stuff/nginx.conf', '/etc/nginx/sites-enabled/stargeo.conf',
        use_sudo=True, backup=False)
    sudo('service nginx reload')

    print(green('Configure celery...'))
    sudo('apt install --yes supervisor')
    files.upload_template('stuff/celery.conf', '/etc/supervisor/conf.d/celery.conf',
        use_sudo=True, backup=False)
    sudo('service supervisor reload')

    # fill stats
    manage('update_statistic_cache')

    execute(deploy)
