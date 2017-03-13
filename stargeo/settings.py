"""
Django settings for stargeo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

INTERNAL_IPS = ['127.0.0.1']

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ['DEBUG'] == 'True'

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_jinja',
    'django_jinja.contrib._humanize',
    'bootstrapform_jinja',
    'datatableview',
    'rest_framework',
    'rest_framework_swagger',
    'rest_framework.authtoken',
    'cacheops',

    'core',
    'legacy',
    'tags',
    'analysis',
    'api',
)
if DEBUG:
    INSTALLED_APPS += ('debug_toolbar', 'django_extensions')

MIGRATION_MODULES = {
    'auth': 'stargeo.auth_migrations'
}

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'stargeo.urls'
LOGIN_REDIRECT_URL = '/'

WSGI_APPLICATION = 'stargeo.wsgi.application'


AUTH_USER_MODEL = 'core.User'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

import dj_database_url
import os

DATABASES = {
    'default': dj_database_url.config(),
}
DATABASES['default']['ENGINE'] = 'transaction_hooks.backends.postgresql_psycopg2'


REDIS = {
    'host': os.environ.get('REDIS_HOST', 'localhost'),
    'port': 6379,
    'db': 3,
    'socket_timeout': 3,
}
BROKER_URL = os.environ.get('BROKER_URL', 'amqp://guest:@127.0.0.1:5672')

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Django registration
ACCOUNT_ACTIVATION_DAYS = 7


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'public')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# For debug toolbar
DEBUG_TOOLBAR_CONFIG = {
    'JQUERY_URL': '/static/jquery.min.js'
}


_TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages"
)

TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "APP_DIRS": True,
        "DIRS": [BASE_DIR + '/templates'],
        "OPTIONS": {
            "match_extension": None,
            # We use default template names for auth things, so we need to intercept them,
            # we hackily exclude email, subject and logged_out templates
            "match_regex": r'(.*\.(j2|jinja)$|(^registration.*(?<!email|bject|d_out)\.\w+$))',
            "context_processors": _TEMPLATE_CONTEXT_PROCESSORS,
            "constants": {
                "FRONTEND": "http://localhost:8082/" if DEBUG else STATIC_URL + 'dist/'
            }
        }
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [BASE_DIR + '/templates'],
        "OPTIONS": {
            "context_processors": _TEMPLATE_CONTEXT_PROCESSORS,
            "debug": DEBUG,
        }
    },
]

TEMPLATE_DEFAULT_EXTENSION = '.j2'


# Cacheops settings
CACHEOPS_REDIS = {
    'host': os.environ.get('REDIS_HOST', 'localhost'),  # redis-server is on same machine
    'port': 6379,         # default redis port
    'db': 1,              # SELECT non-default redis database
    'socket_timeout': 3,  # connection timeout in seconds, optional
}

CACHEOPS = {
    'tags.sampleannotation': {'ops': [], 'timeout': 60 * 60},
}


CELERY_TASK_TIME_LIMIT = 60 * 60 * 12
CELERY_SEND_TASK_ERROR_EMAILS = True
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'no-reply@stargeo.org'

# Logging settings
ADMINS = (
    ('Alexander', 'suor.web@gmail.com'),
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(name)s %(levelname)s [%(asctime)s] %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '../logs/debug.log'),
            'formatter': 'verbose'
        },
        'mail_admins': {'class': 'logging.NullHandler'} if DEBUG else {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
        'boto': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'requests': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Log to console in DEBUG mode
if DEBUG:
    for logger in LOGGING['loggers'].values():
        logger['handlers'] = ['console']


AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY = os.environ['AWS_CREDENTIALS'].split(':')
S3_BUCKETS = {
    'legacy.analysis.df': os.environ['AWS_BUCKET_TEMPLATE'] % 'analysis-df',
    'legacy.analysis.fold_changes': os.environ['AWS_BUCKET_TEMPLATE'] % 'fold-changes',
}

# Django REST framework settings
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'PAGE_SIZE': 10
}

BIOPORTAL_API_KEY = os.environ.get('BIOPORTAL_API_KEY')
