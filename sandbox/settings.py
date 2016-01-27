import os
from oscar import get_core_apps
from oscar import OSCAR_MAIN_TEMPLATE_DIR

ALLOWED_HOSTS = []

BASE_DIR = os.path.dirname(__file__)

OSCARAPI_BLOCK_ADMIN_API_ACCESS = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

DEBUG = True

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': '',
    },
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.flatpages',
    'django.contrib.staticfiles',
    'django_nose',
    'rest_framework',
    'oscarapi',
    'widget_tweaks',
] + get_core_apps()

LANGUAGE_CODE = 'en-us'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'DEBUG' if DEBUG else 'INFO',
        'handlers': ['console',],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s',
        },
        'simple': {
            'format': '[%(asctime)s] %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        # Django loggers
        'django': {
            'propagate': True,
        },
        'django.db': {
            'level': 'WARNING'
        },
        'django.request': {
            'handlers': ['mail_admins',],
            'level': 'ERROR',
            'propagate': False
        },
        # Third party
        'south': {
            'level': 'INFO',
        },
        'sorl.thumbnail': {
            'level': 'ERROR',
        },
        # Suppress output of this debug toolbar panel
        'template_timings_panel': {
            'handlers': ['null'],
        }
    }
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'oscarapi.middleware.HeaderSessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'oscar.apps.basket.middleware.BasketMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

REST_FRAMEWORK = {
    'CHARSET': 'utf-8',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
}

ROOT_URLCONF = 'urls'

SECRET_KEY = 'li0$-gnv)76g$yf7p@(cg-^_q7j6df5cx$o-gsef5hd68phj!4'

SITE_ID = 1

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

TEMPLATE_DEBUG = True
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
    OSCAR_MAIN_TEMPLATE_DIR,
)
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'oscar.apps.search.context_processors.search_form',
    'oscar.apps.promotions.context_processors.promotions',
    'oscar.apps.checkout.context_processors.checkout',
    'oscar.apps.customer.notifications.context_processors.notifications',
    'oscar.core.context_processors.metadata',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True
USE_TZ = True

from oscar.defaults import *
