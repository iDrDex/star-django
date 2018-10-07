from fabric.api import task, execute, env, local, run, sudo, cd, prefix, open_shell, quiet, hide
# from fabric.api import *
from fabric.contrib import django, files
from fabric.colors import green, red


APP_NAME = 'stargeo'
VIRTUALENV_PATH = '~/venv'
PROJECT_PATH = '/home/ubuntu/app'
LOG_PATH = '/home/ubuntu/logs'


django.project('stargeo')
env.cwd = PROJECT_PATH
env.use_ssh_config = True
env.hosts = ['stargeo']
activate = lambda: prefix('source %s/bin/activate' % VIRTUALENV_PATH)


@task
def restart():
    print(green('Restarting celery...'))
    sudo('supervisorctl restart celery')

    restart_app()


def restart_app():
    print(green('Gracefully reloading stargeo gunicorn...'))
    run('kill -HUP `cat /tmp/%s-gunicorn.pid`' % APP_NAME)


def collect_static():
    print(green('Collecting static files...'))
    execute(manage, 'collectstatic --noinput')


@task
def build_frontend():
    print(green('Building frontend...'))
    with cd('frontend'):
        run('npm install')
        run('npm run build')
        run('cp -r dist ../public')


@task
def migrate():
    print(green('Running migrations...'))
    execute(manage, 'migrate')


@task
def manage(cmd):
    with activate():
        run('./manage.py %s' % cmd)


def smart_shell(command=''):
    env_commands = "cd '%s'; %s" % (env.cwd, " && ".join(env.command_prefixes))
    open_shell('%s; %s' % (env_commands, command))

@task
def shell():
    with activate():
        smart_shell('./manage.py shell')

@task
def ssh(command=''):
    with activate():
        if command:
            run(command)
        else:
            smart_shell()

@task
def config():
    local("vim sftp://%s/%s" % (env.host_string, 'app/.env'))


@task
def install_requirements():
    print(green('Installing required Python libraries...'))
    with activate():
        run('pip install --exists-action=s -r requirements.txt')


@task
def install_crontab():
    print(green('Installing new crontab...'))
    app_env = honcho.environ.parse(run('grep ADMIN= .env'))
    name, email = app_env['ADMIN'].split(':')
    run('sed s/{EMAIL}/%s/ stuff/crontab | crontab -' % email)


@task
def deploy():
    execute(sync)
    execute(install_requirements)
    execute(migrate)
    execute(collect_static)
    execute(build_frontend)
    execute(install_crontab)
    execute(restart)


@task
def deploy_fast():
    execute(sync)
    restart_app()  # Not restarting celery, make `fab restart` if you do want that


@task
def dirty_deploy():
    execute(rsync)
    execute(install_requirements)
    execute(migrate)
    execute(collect_static)
    execute(restart)


@task
def dirty_fast():
    execute(rsync)
    restart_app()  # Not restarting celery, make `fab restart` if you do want that


@task
def sync():
    print(green('Fetching git commits and merging...'))
    result = run('git fetch --progress && git merge origin/master', warn_only=True)

    if result.return_code != 0:
        print(red('Git merge returned error, exiting'))
        raise SystemExit()

@task
def rsync():
    """
    An alternative way to send code.

    This sends current directory in its possibly dirty state.
    Use `git pull` or `git fetch` for regular deployments.
    """
    print(green('Uploading files...'))
    local("rsync -avzL --progress --filter=':- .gitignore' -C . %s:%s"
          % (env.host_string, PROJECT_PATH))


import os.path
import honcho.environ
import dj_database_url

DUMP_COMMAND = 'PGPASSWORD=%(PASSWORD)s pg_dump -vC -Upostgres -h %(HOST)s %(NAME)s ' \
               '| gzip --fast --rsyncable > stargeo.sql.gz'

@task
def pull_db(dump='backup'):
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
        local('rsync -avP stargeo:/home/ubuntu/app/stargeo.sql.gz stargeo.sql.gz')
        run('rm stargeo.sql.gz')
    elif dump == 'backup':
        # Alternative: fetch latests db backup
        local('rsync -avP stargeo:/home/ubuntu/db-backups/stargeo.sql.gz stargeo.sql.gz')
    elif dump == 'local':
        print('Using local dump...')
        if not os.path.exists('stargeo.sql.gz'):
            print(red('Local database dump not found (stargeo.sql.gz).\n'
                      'Please use "remote" or "app" dump.'))
            return

    print('Dropping %(NAME)s...' % local_db)
    with quiet():
        local('psql -Upostgres -c "drop database if exists %(NAME)s"' % local_db)

        # Check if database is deleted
        if local('psql -Upostgres -d %(NAME)s -c ""' % local_db, capture=True).succeeded:
            print(red('Database not dropped.\n'
                      'Disconnect all the clients and retry with "fab pull_db:local"'))
            return

    # Load dump
    local('gzip -cd stargeo.sql.gz | psql -Upostgres -f -')


@task
def backup_db():
    """This is designed to be run locally on backup target"""
    app_env = honcho.environ.parse(open('.env').read())
    db = dj_database_url.parse(app_env['DATABASE_URL'])

    with hide('stderr'):
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


@task
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
        run('touch .ssh/config')

    print(green('Installing packages...'))
    sudo('apt update')
    sudo('apt install --yes redis-server')

    execute(install_python)
    execute(install_r)

    print(green('Configuring .env...'))
    if not files.exists('.env'):
        from django.utils.crypto import get_random_string
        files.upload_template('stuff/.env.prod', '.env', {'SECRET_KEY': get_random_string(32)},
                              use_jinja=True, keep_trailing_newline=True)

    # Set up hosts
    files.append('/etc/hosts', ['127.0.0.1 db', '127.0.0.1 redis'], use_sudo=True, shell=True)

    execute(install_postgres)
    execute(install_web)

    print(green('Configure celery...'))
    sudo('apt install --yes supervisor')
    upload_conf('stuff/celery.conf', '/etc/supervisor/conf.d/%s-celery.conf' % APP_NAME,
                use_sudo=True, backup=False)
    sudo('service supervisor reload')

    execute(deploy)

    # fill stats and ontologies
    # FIXME: won't work before keys are set in .env
    manage('update_statistic_cache')
    manage('update_ontologies')


@task
def install_python():
    print(green('Installing Python 3.6...'))
    sudo('add-apt-repository --yes ppa:deadsnakes/ppa')
    sudo('apt-get update')
    sudo('apt-get install --yes python3.6 python3.6-dev python3.6-venv')

    print(green('Creating venv...'))
    run('curl https://bootstrap.pypa.io/get-pip.py | sudo python3.6')
    run('python3.6 -m venv /home/ubuntu/venv')


@task
def install_r():
    print(green('Installing R...'))
    sudo('apt-key adv --keyserver keyserver.ubuntu.com'
         ' --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9')
    sudo('add-apt-repository'
         " 'deb [arch=amd64,i386] https://cran.rstudio.com/bin/linux/ubuntu xenial/'")
    sudo('apt-get update')
    sudo('apt install --yes --no-install-recommends r-base-core r-base-dev')

    run('''echo 'install.packages("meta")' | sudo R --save''')


@task
def install_postgres():
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


@task
def install_web():
    print(green('Setting up Django server...'))
    sudo('apt install --yes supervisor')
    upload_conf('stuff/app-supervisor.conf', '/etc/supervisor/conf.d/%s.conf' % APP_NAME)
    sudo('sudo supervisorctl reload')

    print(green('Configure nginx...'))
    sudo('apt install --yes nginx')
    sudo('rm /etc/nginx/sites-enabled/default', quiet=True)
    execute(conf_nginx)

    # TODO: certbot


@task
def install_node():
    # draft implementation
    print(green('Installing node.js...'))
    run('curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -')
    sudo('apt install --yes nodejs')


@task
def conf_nginx():
    upload_conf('stuff/nginx.conf', '/etc/nginx/sites-enabled/%s.conf' % APP_NAME)
    sudo('service nginx reload')  # `nginx -s reload` for any nginx accessible by path

@task
def offline():
    run('touch offline')

@task
def online():
    run('rm offline')


@task
def docs():
    local('jupyter nbconvert stuff/api.ipynb --template basic --output-dir templates/docs')


# Utilities

from funcy import select_keys

def upload_conf(src_file, dst_file):
    files.upload_template(src_file, dst_file, context=select_keys(str.isupper, globals()),
                          use_sudo=True, backup=False, use_jinja=True)
