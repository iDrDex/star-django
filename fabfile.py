# encoding: utf-8
from fabric.api import *
from fabric.contrib import django, files
from fabric.colors import green, red


__all__ = ('deploy', 'deploy_fast', 'rsync', 'dirty_deploy', 'dirty_fast',
           'shell', 'ssh', 'config',
           'restart', 'manage', 'install_requirements', 'migrate',
           'pull_db', 'backup_db', 'install')


django.project('stargeo')
env.cwd = '/home/ubuntu/app'
env.use_ssh_config = True
env.hosts = ['stargeo']
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
    result = run('git merge', warn_only=True)

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
    run('git pull')

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

DUMP_COMMAND = 'PGPASSWORD=%(PASSWORD)s pg_dump -vC -Upostgres -h %(HOST)s %(NAME)s ' \
               '| gzip --fast --rsyncable > stargeo.sql.gz'

def pull_db(dump='app'):
    app_env = honcho.environ.parse(open('.env').read())
    remote_db = dj_database_url.parse(app_env['REAL_DATABASE_URL'])
    local_db = dj_database_url.parse(app_env['DATABASE_URL'])

    # Make and download database dump
    if dump == 'direct':
        # Dump directly from remote database with local pg_dump
        print('Making database dump...')
        local(DUMP_COMMAND % remote_db)
    elif dump == 'app':
        # Alternative: dump to app-server than rsync here,
        #              useful with slow or flaky internet connection.
        print('Making database dump...')
        run(DUMP_COMMAND % remote_db)
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


def backup_db():
    app_env = honcho.environ.parse(open('.env').read())
    db = dj_database_url.parse(app_env['DATABASE_URL'])

    local(DUMP_COMMAND % db)

    local("mkdir -p ../db-backups")
    local("rdiff-backup --include ./stargeo.sql.gz --exclude '**' . ../db-backups")
    local("rdiff-backup --remove-older-than 30B ../db-backups")
    local("rm stargeo.sql.gz")

    # Restore
    #   gzip -cd ../db-backups/strageo.sql.gz | psql -Upostgres -h db -f -
    # Or
    #   rdiff-backup -r 3D ../db-backups/stargeo.sql.gz stargeo.sql.gz
    #   gzip -cd strageo.sql.gz | psql -Upostgres -h db -f -


def install():
    """
    First deployment script, works with Amazon EC2 Ubuntu 16.04 image.
    To make it work in other systems paths here and in configs should be changed.
    As well as package installations.
    """
    with cd('/home/ubuntu'):
        run('mkdir logs; chmod 777 logs;')
        if not files.exists('app'):
            run('git clone https://github.com/idrdex/star-django.git app')

    print(green('Installing packages...'))
    sudo('apt update')
    sudo('apt install --yes python2.7 python-pip virtualenv')
    sudo('apt install --yes --no-install-recommends r-base-core r-base-dev')
    sudo('apt install --yes redis-server')

    print(green('Configuring .env...'))
    if not files.exists('.env'):
        from django.utils.crypto import get_random_string
        files.upload_template('stuff/.env.prod', '.env', {'SECRET_KEY': get_random_string(32)},
            use_jinja=True, keep_trailing_newline=True)

    # Set up hosts
    files.append('/etc/hosts', ['127.0.0.1 db', '127.0.0.1 redis'], use_sudo=True, shell=True)

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
    sudo('rm /etc/nginx/sites-enabled/default', quiet=True)
    files.upload_template('stuff/nginx.conf', '/etc/nginx/sites-enabled/stargeo.conf',
        use_sudo=True, backup=False)
    sudo('service nginx reload')

    print(green('Configure celery...'))
    sudo('apt install --yes supervisor')
    files.upload_template('stuff/celery.conf', '/etc/supervisor/conf.d/celery.conf',
        use_sudo=True, backup=False)
    sudo('service supervisor reload')

    # fill stats and ontologies
    manage('update_statistic_cache')
    manage('update_ontologies')

    execute(deploy)


def install_node():
    # draft implementation
    print(green('Installing node.js...'))
    run('curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -')
    sudo('apt install --yes nodejs')

    with cd('frontend'):
        run('npm install')
