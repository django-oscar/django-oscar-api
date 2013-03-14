#!/usr/bin/env python
import sys
from coverage import coverage
from optparse import OptionParser
import logging

from django.conf import settings
from oscar import get_core_apps
from oscar.defaults import OSCAR_SETTINGS

# Disable logging
logging.disable(logging.CRITICAL)


if not settings.configured:
    # Tweak some of oscar's defaults
    OSCAR_SETTINGS['OSCAR_EAGER_ALERTS'] = False

    settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    }
                },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.admin',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.sites',
                'oscar_api',
                'south',
                ] + get_core_apps(),
            DEBUG=False,
            SITE_ID=1,
            ROOT_URLCONF='tests.urls',
            NOSE_ARGS=['-s', '--with-spec'],
            # Stuff oscar needs
            HAYSTACK_CONNECTIONS={
                'default': {
                    'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
                }
            },
            **OSCAR_SETTINGS
        )

# Needs to be here to avoid missing SETTINGS env var
from django_nose import NoseTestSuiteRunner


def run_tests(*test_args):
    if 'south' in settings.INSTALLED_APPS:
        from south.management.commands import patch_for_test_db_setup
        patch_for_test_db_setup()

    if not test_args:
        test_args = ['tests']

    # Run tests
    test_runner = NoseTestSuiteRunner(verbosity=1)

    c = coverage(source=['oscar_api'], omit=['*migrations*', '*tests*'])
    c.start()
    num_failures = test_runner.run_tests(test_args)
    c.stop()

    if num_failures > 0:
        sys.exit(num_failures)
    print "Generating HTML coverage report"
    c.html_report()


if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    run_tests(*args)
